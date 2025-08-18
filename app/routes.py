import uuid
from flask import Blueprint, request, jsonify
from app import db
from app.models import User, Room

# Create a Blueprint
bp = Blueprint('main', __name__, url_prefix='/api')

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
        return jsonify({"message": "Login successful", "token": "fake-jwt-token"}), 200
    else:
        return jsonify({"error": "Invalid credentials"}), 401

## --- Rooms ---
@bp.route('/rooms', methods=['POST'])
def create_room():
    user_id = 1  # Placeholder
    room_id = generate_room_id()
    new_room = Room(id=room_id, created_by=user_id)
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

@bp.route('/rooms/<string:room_id>', methods=['PUT'])
def update_room(room_id):
    room = Room.query.get(room_id)
    if not room:
        return jsonify({"error": "Room not found"}), 404
    data = request.get_json()
    new_code = data.get('code_content')
    if new_code is not None:
        room.code_content = new_code
        db.session.commit()
        return jsonify({"message": "Code updated successfully"}), 200
    else:
        return jsonify({"error": "No code_content provided"}), 400

## --- Code Execution ---
@bp.route('/execute/<string:room_id>', methods=['POST'])
def execute_code(room_id):
    room = Room.query.get(room_id)
    if not room:
        return jsonify({"error": "Room not found"}), 404
    code_to_run = room.code_content
    return jsonify({
        "message": "Execution request received",
        "output": f"Simulated output for code:\n{code_to_run}"
    }), 200