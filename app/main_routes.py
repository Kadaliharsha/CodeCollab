from flask import Blueprint, render_template
from app.models import Room
import uuid

# Create a Blueprint for main, user-facing routes
bp = Blueprint('main', __name__)

def generate_room_id():
    return str(uuid.uuid4().hex)[:8]

@bp.route('/room/<string:room_id>')
def room_page(room_id):
    # Check if the room exists in the database
    room = Room.query.get(room_id)
    if not room:
        # Create a new room if it doesn't exist (for direct URL access)
        new_room = Room(id=room_id, created_by=None)  # No user association for direct access
        from app import db
        db.session.add(new_room)
        db.session.commit()
    # Render the HTML page
    return render_template('room.html')