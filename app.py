import uuid
from flask import Flask, request, jsonify
from flask_socketio import SocketIO, join_room, leave_room, emit

# # --In memory database--
# # We use dictionaries to simulate a database
users = {} # Key: username, Value: password_hash
rooms = {} # Key: room_id, Value: room_data dictionary

app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*")

## --Helper Functions--

def generate_room_id():
	"""Generate a unique, simple room ID."""
	return str(uuid.uuid4().hex)[:8]

## -- API Endpoints --

@app.route('/api/auth/register', methods=['POST'])
def register_user():
	data = request.get_json()
	username = data.get('username')
	password = data.get('password')
	if not username or not password:
		return jsonify({"error": "Username and password are required"}), 400
	if username in users: 
		return jsonify({"error": "Username already exists"}), 400
	users[username] = password
	print("Current users: ", users) # For Debugging
	return jsonify({"message": f"User {username} registered successfully!"}), 201

@app.route('/api/auth/login', methods=["POST"])
def login_user():
	data = request.get_json()
	username = data.get('username')
	password = data.get('password')
	if users.get(username) == password:
		return jsonify({"message" : " Login successful", "token": "fake-jwt-token"}), 200
	else:
		return jsonify({"error": "Invalid credentials"}), 401
    
@app.route('/api/rooms', methods=["POST"])
def create_room():
	room_id = generate_room_id()
	rooms[room_id] = {
		"id": room_id,
		"code-content": "# Welcome to CodeCollab!",
		"users": []
	}
	print("Current rooms:", rooms) # For debugging
	return jsonify({"message": "Room created" , "room_id": room_id}), 201

@app.route('/api/rooms/<string:room_id>', methods=["GET"])
def get_room(room_id):
	room = rooms.get(room_id)
	if room:
		return jsonify(room), 200
	else:
		return jsonify({"error": "Room not found"}), 404
    
@app.route('/api/rooms/<string:room_id>/join', methods=['PUT'])
def update_room(room_id):
	if room_id not in rooms:
		return jsonify({"error": "Room not found"}), 404
	data = request.get_json()
	new_code = data.get('code_content')
	if new_code is not None:
		rooms[room_id]['code-content'] = new_code
		print(f"Room {room_id} updated:", rooms[room_id]) # For debugging
		return jsonify({"message": "Code updated successfully!"}), 200
	else:
		return jsonify({"error": "Code content is required"}), 400

@app.route('/api/execute/<string:room_id>/execute', methods=['POST'])
def execute_code(room_id):
	if room_id not in rooms:
		return jsonify({"error" : "Room not found"}), 404
	code_to_run = rooms[room_id].get('code-content')
	print(f"Executing code in roon {room_id}:\n{code_to_run}") 
	return jsonify({
		"message": "Execution request received",
		"output": "Hello, friend! \n This is the output of your code."
	}), 200
    

# -- Socket.IO Events --
@socketio.on('join_room')
def handle_join_room(data):
	room_id = data.get('room_id')
	username = data.get('username')
	join_room(room_id)
	if room_id in rooms:
		# Add user to room if not already there
		if username not in rooms[room_id]['users']:
			rooms[room_id]['users'].append(username)
		# Broadcast to other users in the room
		emit('user_joined', {'username': username}, to=room_id, include_self=False)
		emit('code_update', {'code_content': rooms[room_id]['code-content']}, to=room_id)

@socketio.on('request_existing_users')
def handle_request_existing_users(data):
	room_id = data.get('room_id')
	if room_id in rooms:
		# Create user objects for all users in the room
		users_in_room = [{'id': i, 'username': username} for i, username in enumerate(rooms[room_id]['users'])]
		emit('existing_users', {'users': users_in_room})

@socketio.on('leave_room')
def handle_leave_room(data):
	room_id = data.get('room_id')
	username = data.get('username')
	leave_room(room_id)
	if room_id in rooms and username in rooms[room_id]['users']:
		rooms[room_id]['users'].remove(username)
		emit('user_left', {'username': username}, to=room_id)

@socketio.on('end_session')
def handle_end_session(data):
	room_id = data.get('room_id')
	if room_id in rooms:
		# Broadcast session ended to all users in the room
		emit('session_ended', {'room_id': room_id}, to=room_id)
		# Remove the room
		del rooms[room_id]

@socketio.on('code_change')
def handle_code_change(data):
	room_id = data.get('room_id')
	code_content = data.get('code_content')
	if room_id in rooms:
		rooms[room_id]['code-content'] = code_content
		emit('code_update', {'code_content': code_content}, to=room_id, include_self=False)

# -- Main Execution ---
if __name__ == "__main__":
	socketio.run(app, debug=True, port=5001)