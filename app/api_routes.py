import uuid
from flask import Blueprint, request, jsonify
from app import db, socketio
from app.models import User, Room, Problem, TestCase
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
from flask_socketio import join_room, leave_room, emit
from app.code_executor import run_code

# Create a Blueprint for API routes
bp = Blueprint('api', __name__, url_prefix='/api')

# ... (Authentication and other routes remain the same) ...
def generate_room_id():
    return str(uuid.uuid4().hex)[:8]

@bp.route('/auth/register', methods=['POST'])
def register_user():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    if not username or not password:
        return jsonify({"error": "Username and password are required"}), 400
    if User.query.filter_by(username=username).first():
        return jsonify({"error": "Username already exists"}), 409
    new_user = User(username=username)
    new_user.set_password(password)
    db.session.add(new_user)
    db.session.commit()
    return jsonify({"message": f"User {username} registered successfully"}), 201

@bp.route('/auth/login', methods=['POST'])
def login_user():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    user = User.query.filter_by(username=username).first()
    if user and user.check_password(password):
        access_token = create_access_token(identity=str(user.id))
        return jsonify(access_token=access_token), 200
    else:
        return jsonify({"error": "Invalid credentials"}), 401

@bp.route('/rooms', methods=['POST'])
@jwt_required()
def create_room():
    current_user_id = get_jwt_identity()
    room_id = generate_room_id()
    new_room = Room(id=room_id, created_by=current_user_id)
    db.session.add(new_room)
    db.session.commit()
    return jsonify({"message": "Room created", "room_id": room_id}), 201

@bp.route('/rooms/<string:room_id>', methods=['GET'])
def get_room(room_id):
    room = Room.query.get(room_id)
    if not room:
        return jsonify({"error": "Room not found"}), 404
    problem_details = {}
    if room.problem_id:
        problem = Problem.query.get(room.problem_id)
        if problem:
            problem_details = {
                "title": problem.title,
                "description": problem.description,
                "template_code": problem.template_code
            }
    return jsonify({
        "id": room.id,
        "code_content": room.code_content,
        "created_by": room.created_by,
        "language": room.language,
        "problem": problem_details
    }), 200

@bp.route('/problems', methods=['GET'])
def get_problems():
    problems = Problem.query.all()
    problem_list = [{"id": p.id, "title": p.title} for p in problems]
    return jsonify(problem_list), 200


## --- WebSocket Event Handlers ---
@socketio.on('join_room')
def handle_join_room(data):
    room_id = data.get('room_id')
    username = data.get('username', 'A user')
    join_room(room_id)
    print(f"{username} has joined room {room_id}")
    emit('user_joined', {'username': username}, to=room_id)

@socketio.on('code_change')
def handle_code_change(data):
    room_id = data.get('room_id')
    new_code = data.get('code_content')
    print(f"[code_change] Received for room_id: {room_id}, code_content: {new_code[:30]}...")
    room = Room.query.get(room_id)
    if room:
        print(f"[code_change] Room found: {room_id}, updating code.")
        room.code_content = new_code
        db.session.commit()
        emit('code_update', {'code_content': new_code}, to=room_id, include_self=False)
    else:
        print(f"[code_change] Room NOT found: {room_id}")

@socketio.on('leave_room')
def handle_leave_room(data):
    room_id = data.get('room_id')
    room = Room.query.get(room_id)
    if room:
        room.problem_id = None
        db.session.commit()
        emit('lobby_activated', {}, to=room_id)
        
@socketio.on('language_change')
def handle_language_change(data):
    room_id = data.get('room_id')
    new_language = data.get('language')
    room = Room.query.get(room_id)
    if room:
        room.language = new_language
        db.session.commit()
    emit('language_updated', {'language': new_language}, to=room_id, include_self=False)

# --- NEW: WebSocket Handler for Loading a Problem ---
@socketio.on('load_problem')
def handle_load_problem(data):
    """Handles a request to load a problem into a room."""
    room_id = data.get('room_id')
    problem_id = data.get('problem_id')

    room = Room.query.get(room_id)
    problem = Problem.query.get(problem_id)

    if room and problem:
        # Link the problem to the room and save to DB
        room.problem_id = problem.id
        room.code_content = problem.template_code # Reset code to template
        db.session.commit()

        # Fetch the full room data to send back
        problem_details = {
            "title": problem.title,
            "description": problem.description,
            "template_code": problem.template_code
        }
        room_data = {
            "id": room.id,
            "code_content": room.code_content,
            "language": room.language,
            "problem": problem_details
        }
        
        # Broadcast to everyone in the room that the problem is loaded
        emit('problem_loaded', room_data, to=room_id)

@socketio.on('execute_code')
def handle_execute_code(data):
    """Handles a request to execute code (Run button)."""
    room_id = data.get('room_id')
    language = data.get('language', 'python')
    # FIXED: Get the code directly from the data sent by the frontend
    code_to_run = data.get('code', '') 
    
    # We still get the room to ensure it exists, but we don't need its saved code
    room = Room.query.get(room_id)
    if not room:
        return 

    # Call run_code without test_input_args for a simple "Run"
    output, error = run_code(code_to_run, language)
    result = {"output": output, "error": error}
    emit('execution_result', result, to=room_id)

@socketio.on('submit_code')
def handle_submit_code(data):
    """
    Handles a code submission, runs it against all test cases,
    and broadcasts the final verdict.
    """
    room_id = data.get('room_id')
    language = data.get('language', 'python')
    # FIXED: Get the code directly from the data sent by the frontend
    user_code = data.get('code', '')

    room = Room.query.get(room_id)
    if not room or not room.problem_id:
        emit('submit_result', {'verdict': 'Error', 'details': 'No problem associated with this room.'}, to=room_id)
        return

    problem = Problem.query.get(room.problem_id)
    if not problem or not problem.test_cases:
        emit('submit_result', {'verdict': 'Error', 'details': 'Could not find test cases for this problem.'}, to=room_id)
        return

    passed_all_tests = True
    for i, test_case in enumerate(problem.test_cases):
        # Pass the test case input as the third argument
        actual_output, error = run_code(user_code, language, test_case.input_data)
        if error:
            verdict = "Runtime Error"
            details = f"Test Case #{i+1} failed with an error:\n{error}"
            passed_all_tests = False
            break
        if actual_output.strip() != test_case.expected_output.strip():
            verdict = "Wrong Answer"
            details = f"Test Case #{i+1} failed.\nExpected: {test_case.expected_output}\nGot: {actual_output}"
            passed_all_tests = False
            break
    if passed_all_tests:
        verdict = "Accepted"
        details = f"Congratulations! You passed all {len(problem.test_cases)} test cases."
    emit('submit_result', {'verdict': verdict, 'details': details}, to=room_id)