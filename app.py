# import uuid
# from flask import Flask, request, jsonify

# # --In memory database--
# # We use dictionaries to simulate a database
# users = {} # Key: username, Value: password_hash
# rooms = {} # Key: room_id, Value: room_data dictionary

# app = Flask(__name__)

# # --Helper Functions--

# def generate_room_id():
#     """Generate a unique, simple room ID."""
#     # In a real app, you might make this more human-readable.
#     return str(uuid.uuid4().hex)[:8]

# # -- API Endpoints --

# # --- Authentication ---
# @app.route('/api/auth/register', methods=['POST'])
# def register_user():
#     data = request.get_json()
#     username = data.get('username')
#     password = data.get('password')
    
#     if not username or not password:
#         return jsonify({"error": "Username and password are required"}), 400
    
#     if username in users: 
#         return jsonify({"error": "Username already exists"}), 400
    
#     # In a real app, you would hash the password here!
#     users[username] = password
#     print("Current users: ", users) # For Debugging
#     return jsonify({"message": f"User {username} registered successfully!"}), 201

# @app.route('/api/auth/login', methods=["POST"])
# def login_user():
#     data = request.get_json()
#     username = data.get('username')
#     password = data.get('password')
    
#     # In a real app, you'd compare paswword hashes
#     if users.get(username) == password:
#         return jsonify({"message" : " Login successful", "token": "fake-jwt-token"}), 200
#     else:
#         return jsonify({"error": "Invalid credentials"}), 401
    
# # -- Rooms -- 
# @app.route('/api/rooms', methods=["POST"])
# def create_room():
#     room_id = generate_room_id()
#     rooms[room_id] = {
#         "id": room_id,
#         "code-content": "# Welcome to CodeCollab!",
#         "users": []
#     }
#     print("Current rooms:", rooms) # For debugging
#     return jsonify({"message": "Room created" , "room_id": room_id}), 201

# @app.route('/api/rooms/<string:room_id>', methods=["GET"])
# def get_room(room_id):
#     room = rooms.get(room_id)
#     if room:
#         return jsonify(room), 200
#     else:
#         return jsonify({"error": "Room not found"}), 404
    
# @app.route('/api/rooms/<string:room_id>/join', methods=['PUT'])
# def update_room(room_id):
#     if room_id not in rooms:
#         return jsonify({"error": "Room not found"}), 404
    
#     data = request.get_json()
#     new_code = data.get('code_content')
    
#     if new_code is not None:
#         rooms[room_id]['code-content'] = new_code
#         print(f"Room {room_id} updated:", rooms[room_id]) # For debugging
#         return jsonify({"message": "Code updated successfully!"}), 200
#     else:
#         return jsonify({"error": "Code content is required"}), 400

# # -- Code Execution --
# @app.route('/api/execute/<string:room_id>/execute', methods=['POST'])
# def execute_code(room_id):
#     if room_id not in rooms:
#         return jsonify({"error" : "Room not found"}), 404
    
#     code_to_run = rooms[room_id].get('code-content')
#     print(f"Executing code in roon {room_id}:\n{code_to_run}") 
    
#     return jsonify({
#         "message": "Execution request received",
#         "output": "Hello, friend! \n This is the output of your code."
#     }), 200
    
# # -- Main Execution ---
# if __name__ == "__main__":
#     app.run(debug=True, port=5001)