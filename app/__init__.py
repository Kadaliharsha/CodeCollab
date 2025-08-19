from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_jwt_extended import JWTManager
from flask_socketio import SocketIO
from flask_cors import CORS
from config import Config

# Initialize the database
db = SQLAlchemy()
jwt = JWTManager()
socketio = SocketIO(cors_allowed_origins="*")

def create_app(config_class=Config):
    """Creates and configures the Flask application."""
    app = Flask(__name__)
    app.config.from_object(config_class)
    
    # Enable cors for the flask app
    CORS(app)
    
    # Initialize extensions
    db.init_app(app)
    jwt.init_app(app)
    socketio.init_app(app)
    
    # Import and register blueprints
    from app.api_routes import bp as api_blueprint
    from app.main_routes import bp as main_blueprint
    app.register_blueprint(api_blueprint)
    app.register_blueprint(main_blueprint)
    
    return app