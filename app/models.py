from app import db
from werkzeug.security import generate_password_hash, check_password_hash

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class Room(db.Model):
    id = db.Column(db.String(10), primary_key=True)
    code_content = db.Column(db.Text, nullable=True, default="# Welcome to your CodeCollab room!\nprint('Hello, friend!')")
    created_by = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    problem_id = db.Column(db.Integer, db.ForeignKey('problem.id'), nullable=True)
    
    # --- NEW: Add a column to store the current language ---
    language = db.Column(db.String(20), nullable=False, default='python')


class Problem(db.Model):
    """Represents a coding problem."""
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=False) 
    template_code = db.Column(db.Text, nullable=True)
    test_cases = db.relationship('TestCase', backref='problem', lazy=True, cascade="all, delete-orphan")

class TestCase(db.Model):
    """Represents a single test case for a Problem."""
    id = db.Column(db.Integer, primary_key=True)
    input_data = db.Column(db.Text, nullable=False)
    expected_output = db.Column(db.Text, nullable=False)
    is_hidden = db.Column(db.Boolean, default=True, nullable=False)
    problem_id = db.Column(db.Integer, db.ForeignKey('problem.id'), nullable=False)
