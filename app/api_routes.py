import uuid
from flask import Blueprint, request, jsonify
from app import db, socketio
from app.models import User, Room
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
from flask_socketio import join_room, emit
from app.code_executor import run_python_code

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
    try:
        creator_id = int(current_user_id)
    except (TypeError, ValueError):
        return jsonify({"error": "Invalid user identity"}), 400

    room_id = generate_room_id()
    new_room = Room()
    new_room.id = room_id
    new_room.created_by = creator_id
    db.session.add(new_room)
    db.session.commit()
    return jsonify({"message": "Room created", "room_id": room_id}), 201

@bp.route('/rooms/<string:room_id>', methods=['GET'])
def get_room(room_id):
    room = Room.query.get(room_id)
    if room:
        return jsonify({
            "id": room.id,
            "code_content": room.code_content,
            "created_by": room.created_by
        }), 200
    else:
        return jsonify({"error": "Room not found"}), 404

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
    room = Room.query.get(room_id)
    if not room:
        return
    
    output, error = run_python_code(room.code_content)
    
    result = {
        "output": output,
        "error": error
    }
    
    # Broadcast the result to EVERYONE in the room
    emit('execution_result', result, to=room_id)
    
# ## --- Frontend route ---
# @bp.route('/room/string:room_id>')
# def room_page(room_id):
#     room = Room.query.get(room_id)
#     if not room:
#         return "Room not found", 404
#     return render_template("room.html")