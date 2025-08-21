import uuid
from flask import Blueprint, request, jsonify
from app import db, socketio
from app.models import User, Room, Problem, TestCase
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
from flask_socketio import join_room, emit
from app.code_executor import run_code
from sqlalchemy.orm import joinedload

# Create a Blueprint
bp = Blueprint('api', __name__, url_prefix='/api')

def generate_room_id():
    return str(uuid.uuid4().hex)[:8]

## --- Authentication ---
@bp.route('/auth/register', methods=['POST'])
def register_user():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    
    if not username or not password:
        return jsonify({"error": "Username and password are required"}), 400
    if User.query.filter_by(username=username).first():
        return jsonify({"error": "Username already exists"}), 409
    
    new_user = User()
    new_user.username = username
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
        # The 'identity' is the data we want to store in the token.
        # It must be a string, so we convert the user.id.
        access_token = create_access_token(identity=str(user.id))
        return jsonify(access_token=access_token), 200
    else:
        return jsonify({"error": "Invalid credentials"}), 401

## --- Rooms ---
@bp.route('/rooms', methods=['POST'])
@jwt_required() # This decorator PROTECTS the route
def create_room():
    # Get the user ID from the JWT token
    current_user_id = get_jwt_identity()
    # try:
    #     creator_id = int(current_user_id)
    # except (TypeError, ValueError):
    #     return jsonify({"error": "Invalid user identity"}), 400

    room_id = generate_room_id()
    new_room = Room()
    new_room.id = room_id
    new_room.created_by = current_user_id
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
        "problem": problem_details
    }), 200

@bp.route('/problems', methods=['GET'])
def get_problems():
    problems = Problem.query.all()
    problem_list =[{"id": p.id, "title": p.title} for p in problems]
    return jsonify(problem_list), 200

# -- code execution ---

@bp.route('/rooms/<string:room_id>', methods=['PUT'])
@jwt_required() # This decorator PROTECTS the route
def update_room(room_id):
    room = Room.query.get(room_id)
    if not room:
        return jsonify({"error": "Room not found"}), 404
    
    # Optional: Check if the current user is the one who created the room
    current_user_id = get_jwt_identity()
    if room.created_by != int(current_user_id):
        return jsonify({"error": "Forbidden"}), 403

    data = request.get_json()
    new_code = data.get('code_content')
    if new_code is not None:
        room.code_content = new_code
        db.session.commit()
        return jsonify({"message": "Code updated successfully"}), 200
    else:
        return jsonify({"error": "No code_content provided"}), 400

## --- Code Execution ---
# @bp.route('/execute/<string:room_id>', methods=['POST'])
# def execute_code(room_id):
#     room = Room.query.get(room_id)
#     if not room:
#         return jsonify({"error": "Room not found"}), 404
#     code_to_run = room.code_content
    
#     # Call our new Docker execution service
#     output, error = run_python_code(code_to_run)

#     if error:
#         return jsonify({"error": error}), 400

#     return jsonify({
#         "message": "Execution request received",
#         "output": output,
#         "error": error
#     }), 200
    
## --- Websocket Event Handlers ---
@socketio.on('join_room')
def handle_join_room(data):
    """Handling a user joining a room"""
    room_id = data.get('room_id')
    username = data.get('username', 'A user') # In a real app we get this from JWT
    
    # Add a user to socket.io room
    join_room(room_id)
    
    print(f"{username} has joined room {room_id}")
    # Announce that a user has joined to others in the room
    emit('user_joined', {'username': username}, to=room_id)
    
@socketio.on('code_change')
def handle_code_change(data):
    """Handles changes to the code editor."""
    room_id = data.get('room_id')
    new_code = data.get('code')
    
    # Save the new code to the database
    room = Room.query.get(room_id)
    if room:
        room.code_content = new_code
        db.session.commit()
        
    # Broadcast the change to all other clients in the room
    emit('code_updated', {'code': new_code}, to=room_id, include_self=False)

# New Websocket handler for code execution
@socketio.on('execute_code')
def handle_execute_code(data):
    """Handles a request to execute code and broadcasts the result."""
    room_id = data.get('room_id')
    custom_input = data.get('input', '')
    language = data.get('language','python')
    
    room = Room.query.get(room_id)
    if not room:
        return
    
    code_to_run = room.code_content
    output, error = run_code(code_to_run, language, custom_input)
    # Log for debugging
    try:
        print(f"[execute_code] room={room_id} language={language} output=\n{output}")
        if error:
            print(f"[execute_code][ERROR] room={room_id} language={language} error=\n{error}")
    except Exception:
        pass
    
    result = {
        "output": output,
        "error": error
    }
    
    # Broadcast the result to EVERYONE in the room
    emit('execution_result', result, to=room_id)

@socketio.on('language_changed')
def handle_language_changed(data):
    """Broadcast language change to all other clients in the room."""
    room_id = data.get('room_id')
    language = data.get('language', 'python')
    if not room_id:
        return
    emit('language_updated', { 'language': language }, to=room_id, include_self=False)
    
@socketio.on('submit_code')
def handle_submit_code(data):
    """
    Handles a code submission, runs it against all test cases,
    and broadcasts the final verdict.
    """
    room_id = data.get('room_id')
    language = data.get('language', 'python')
    
    room = Room.query.get(room_id)
    if not room or not room.problem_id:
        emit('submit_result', {'verdict': 'Error', 'details': 'No problem associated with this room.'}, to=room_id)
        return

    problem = Problem.query.get(room.problem_id)
    if not problem or not problem.test_cases:
        emit('submit_result', {'verdict': 'Error', 'details': 'Could not find test cases for this problem.'}, to=room_id)
        return

    user_code = room.code_content
    passed_all_tests = True
    verdict = ""
    details = ""

    for i, test_case in enumerate(problem.test_cases):
        # Run the user's code with the test case's input
        actual_output, error = run_code(user_code, language, test_case.input_data)

        # Check for runtime errors
        if error:
            verdict = "Runtime Error"
            details = f"Test Case #{i+1} failed with an error:\n{error}"
            passed_all_tests = False
            break # Stop testing if one case fails

        # Compare the actual output with the expected output
        # We strip whitespace to be more lenient with formatting
        if actual_output.strip() != test_case.expected_output.strip():
            verdict = "Wrong Answer"
            details = f"Test Case #{i+1} failed.\nExpected: {test_case.expected_output}\nGot: {actual_output}"
            passed_all_tests = False
            break # Stop testing if one case fails

    if passed_all_tests:
        verdict = "Accepted"
        details = f"Congratulations! You passed all {len(problem.test_cases)} test cases."
    # Broadcast the final result to everyone in the room
    emit('submit_result', {'verdict': verdict, 'details': details}, to=room_id)

# ## --- Frontend route ---
# @bp.route('/room/string:room_id>')
# def room_page(room_id):
#     room = Room.query.get(room_id)
#     if not room:
#         return "Room not found", 404
#     return render_template("room.html")