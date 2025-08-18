from app import db
from werkzeug.security import generate_password_hash, check_password_hash

class User(db.Model):
    """User model."""
    id = db.Column(db.Integer, primary_key = True)
    username = db.Column(db.String(150), unique = True, nullable = False)
    password_hash = db.Column(db.String(255), nullable = False)
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
        
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
class Room(db.Model):
    """Room model."""
    id = db.Column(db.String(10), primary_key=True)
    code_content = db.Column(db.Text, nullable=True, default="# Welcome to your CodeCollab room\n print('Hello,friend!')")
    created_by = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)