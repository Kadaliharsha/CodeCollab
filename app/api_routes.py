import uuid
from flask import Blueprint, request, jsonify
from app import db, socketio
from app.models import User, Room, Problem, TestCase, SessionEvent
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity, decode_token
from flask_socketio import join_room, leave_room, emit
from app.code_executor import run_code
from datetime import timedelta


# Create a Blueprint for API routes
bp = Blueprint('api', __name__, url_prefix='/api')

# Global dictionary to track active users in rooms
# Format: {room_id: [{'username': 'user1', 'socket_id': 'sid1'}, ...]}
active_users = {}

def record_event(room_id, event_type, payload=None):
    event = SessionEvent()
    event.room_id = str(room_id)
    event.event_type = event_type
    event.payload = payload or {}
    db.session.add(event)
    db.session.commit()

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
        access_token = create_access_token(identity=str(user.id))
        return jsonify(access_token=access_token), 200
    else:
        return jsonify({"error": "Invalid credentials"}), 401
    
@bp.route('/auth/forgot', methods=['POST'])
def forgot_password():
    data = request.get_json() or {}
    username = data.get('username')
    if not username:
        return jsonify({"error": "username is required"}), 400

    user = User.query.filter_by(username=username).first()
    if not user:
        return jsonify({"message": "If the user exists, a reset link has been sent "}), 200
    
    reset_token = create_access_token(identity=str(user.id),
                                      additional_claims={"purpose": "password_reset"},
                                      expires_delta=timedelta(minutes=15))
    
    return jsonify({
        "message": "Reset link generated.",
        "reset_token": reset_token
    }), 200

@bp.route('/auth/reset', methods=['POST'])
def reset_password():
    data = request.get_json() or {}
    token = data.get('token')
    new_password = data.get('new_password')
    if not token or not new_password:
        return jsonify({"error": "token and new_password are required"}), 400
    
    try:
        decoded = decode_token(token)
        if decoded.get("claims", {}).get("purpose") != "password_reset":
            return jsonify({"error": "Invalid token type"}), 400
        user_id = decoded.get("sub")
        user = User.query.get(int(user_id)) if user_id else None
        if not user:
            return jsonify({"error": "Invalid token"}), 400
        user.set_password(new_password)
        db.session.commit()
        return jsonify({"message": "Password has been reset successfully."}), 200
    except Exception:
        return jsonify({"error": "Invalid or expired token"}), 400
    
@bp.route('/rooms', methods=['POST'])
@jwt_required()
def create_room():
    current_user_id = get_jwt_identity()
    room_id = generate_room_id()
    new_room = Room()
    new_room.id = room_id
    new_room.created_by = current_user_id
    db.session.add(new_room)
    db.session.commit()
    record_event(room_id, "create_room", {"created_by": current_user_id})
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

@bp.route('/test-socket', methods=['POST'])
def test_socket():
    """Test endpoint to verify socket connection"""
    data = request.get_json()
    room_id = data.get('room_id', 'test')
    message = data.get('message', 'Hello from test endpoint')
    
    # Try to emit to the room
    print(f"[test-socket] Testing emit to room {room_id}")
    socketio.emit('code_update', {'code_content': message}, to=room_id)
    print(f"[test-socket] Emit completed")
    
    return jsonify({"status": "test message sent", "room_id": room_id}), 200

@bp.route('/sessions/<string:room_id>/timeline', methods=['GET'])
def get_session_timeline(room_id):
    events = db.session.query(SessionEvent).filter_by(room_id=room_id).order_by(SessionEvent.created_at).all()
    
    timeline = []
    for event in events:
        timeline.append({
            'id': event.id,
            'event_type': event.event_type,
            'payload': event.payload,
            'created_at': event.created_at.isoformat() if event.created_at else None
        })
        
    return jsonify({
        'room_id': room_id,
        'total_events': len(timeline),
        'timeline': timeline
    }), 200
    
@bp.route('/sessions/<room_id>/summary', methods=["GET"])
def get_session_summary(room_id):
    events = db.session.query(SessionEvent).filter_by(room_id=room_id).all()
    
    event_counts = {}
    for event in events:
        event_counts[event.event_type] = event_counts.get(event.event_type, 0) + 1
        
    first_event = db.session.query(SessionEvent).filter_by(room_id=room_id).order_by(SessionEvent.created_at).first()
    last_event = db.session.query(SessionEvent).filter_by(room_id=room_id).order_by(SessionEvent.created_at.desc()).first()
    
    return jsonify({
        'room_id': room_id,
        'total_events': len(events),
        'event_counts': event_counts,
        'session_start': first_event.created_at.isoformat() if first_event else None,
        'session_end': last_event.created_at.isoformat() if last_event else None,
        'duration_minutes': None
    }), 200

## --- WebSocket Event Handlers ---
@socketio.on('connect')
def handle_connect():
    print(f"Client connected")
    emit('connected', {'message': 'Connected to server'})

@socketio.on('test_message')
def handle_test_message(data):
    """Simple test event to verify socket communication"""
    room_id = data.get('room_id', 'test')
    message = data.get('message', 'Test message')
    print(f"[test_message] Received test message: {message} for room: {room_id}")
    
    # Echo back to the same client
    emit('test_response', {'message': f'Echo: {message}', 'room_id': room_id})
    
    # Also try to broadcast to the room
    emit('code_update', {'code_content': f'Test broadcast: {message}'}, to=room_id)
    print(f"[test_message] Sent test broadcast to room {room_id}")

@socketio.on('join_room')
def handle_join_room(data):
    room_id = data.get('room_id')
    username = data.get('username', 'A user')
    print(f"User {username} joining room {room_id}")
    
    # DEBUG: Check current rooms before joining
    from flask_socketio import rooms
    before_rooms = rooms()
    print(f"[join_room] Before joining: {username} is in rooms: {before_rooms}")
    
    join_room(room_id)
    record_event(room_id, "join", {"username": username})
    print(f"User {username} joined socket room {room_id}")
    
    # DEBUG: Check current rooms after joining
    after_rooms = rooms()
    print(f"[join_room] After joining: {username} is in rooms: {after_rooms}")
    
    # Track the user in the active_users dictionary
    if room_id not in active_users:
        active_users[room_id] = []
    
    # Add user if not already in the room
    if username not in [user['username'] for user in active_users[room_id]]:
        active_users[room_id].append({'username': username})
        print(f"Added {username} to room {room_id}. Active users: {[u['username'] for u in active_users[room_id]]}")
    
    # Broadcast to other users in the room
    emit('user_joined', {'username': username}, to=room_id, include_self=False)
    print(f"Emitted user_joined event for {username} to room {room_id}")

@socketio.on('request_existing_users')
def handle_request_existing_users(data):
    room_id = data.get('room_id')
    print(f"Request for existing users in room: {room_id}")
    
    # Return the actual active users in the room
    if room_id in active_users:
        users_in_room = [{'id': i, 'username': user['username']} for i, user in enumerate(active_users[room_id])]
        print(f"Found users in room {room_id}: {users_in_room}")
        emit('existing_users', {'users': users_in_room})
    else:
        print(f"No active users found for room {room_id}")
        emit('existing_users', {'users': []})

@socketio.on('code_change')
def handle_code_change(data):
    room_id = data.get('room_id')
    # Handle both parameter names for compatibility
    new_code = data.get('code_content') or data.get('code')
    message_id = data.get('message_id')  # Get the message ID from the client
    print(f"[code_change] Received for room_id: {room_id}, code_content: {new_code[:30] if new_code else 'None'}..., message_id: {message_id}")
    
    if not new_code:
        print(f"[code_change] No code content received!")
        return
    
    # DEBUG: Check if anyone is actually in this room
    from flask_socketio import rooms
    current_rooms = rooms()
    print(f"[code_change] Current socket rooms: {current_rooms}")
    print(f"[code_change] Requesting client is in rooms: {current_rooms}")
    
    # First try to get the room from database
    room = Room.query.get(room_id)
    if room:
        print(f"[code_change] Room found: {room_id}, updating code.")
        room.code_content = new_code
        db.session.commit()
        record_event(room_id, "code_change", {"message_id": message_id, "length": len(new_code or "")})
        # Broadcast to ALL users in the room (including sender for perfect sync)
        print(f"[code_change] Emitting code_update to room {room_id} with content: {new_code[:30]}...")
        emit('code_update', {'code_content': new_code, 'message_id': message_id}, to=room_id, include_self=False)
        print(f"[code_change] Emit completed for room {room_id}")
    else:
        print(f"[code_change] Room NOT found: {room_id}, creating it...")
        # Create the room if it doesn't exist
        try:
            new_room = Room()
            new_room.id = room_id
            new_room.created_by = None
            new_room.code_content = new_code
            db.session.add(new_room)
            record_event(room_id, "code_change", {"message_id": message_id, "length": len(new_code or "")})
            db.session.commit()
            print(f"[code_change] Created new room: {room_id}")
            # Broadcast to ALL users in the room
            print(f"[code_change] Emitting code_update to room {room_id} with content: {new_code[:30]}...")
            emit('code_update', {'code_content': new_code, 'message_id': message_id}, to=room_id, include_self=False)
            print(f"[code_change] Emit completed for room {room_id}")
        except Exception as e:
            print(f"[code_change] Error creating room: {e}")
            # Still broadcast the update even if room creation fails
            record_event(room_id, "code_change", {"message_id": message_id, "length": len(new_code or "")})
            print(f"[code_change] Emitting code_update to room {room_id} (fallback) with content: {new_code[:30]}...")
            emit('code_update', {'code_content': new_code, 'message_id': message_id}, to=room_id, include_self=False)
            print(f"[code_change] Emit completed for room {room_id} (fallback)")

@socketio.on('leave_room')
def handle_leave_room(data):
    room_id = data.get('room_id')
    username = data.get('username')
    print(f"User {username} leaving room {room_id}")
    
    # Leave the socket room
    leave_room(room_id)
    
    # Remove user from active_users tracking
    if room_id in active_users:
        active_users[room_id] = [user for user in active_users[room_id] if user['username'] != username]
        print(f"Removed {username} from room {room_id}. Remaining users: {[u['username'] for u in active_users[room_id]]}")
    record_event(room_id, "leave", {"username": username})
    
    # Emit user_left event to remaining users
    print(f"Emitting user_left event for {username} to room {room_id}")  # Debug log
    emit('user_left', {'username': username}, to=room_id)
    
    # Also emit lobby_activated if needed
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
        record_event(room_id, "language_change", {"language": new_language})
        
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
        record_event(room_id, "load_problem", {"problem_id": problem_id})

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
    record_event(room_id, "run", {"language": language, "has_error": bool(error)})

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

    verdict = "Accepted"
    details = ""
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
        record_event(room_id, "submit", {"verdict": verdict})
        emit('submit_result', {'verdict': verdict, 'details': details}, to=room_id)