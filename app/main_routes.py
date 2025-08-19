from flask import Blueprint, render_template
from app.models import Room

# Create a Blueprint for main, user-facing routes
bp = Blueprint('main', __name__)

@bp.route('/room/<string:room_id>')
def room_page(room_id):
    # Check if the room exists in the database
    room = Room.query.get(room_id)
    if not room:
        return "Room not found", 404
    # Render the HTML page
    return render_template('room.html')