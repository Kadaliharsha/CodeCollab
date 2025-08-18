from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from config import Config

# Initialize the database
db = SQLAlchemy()

def create_app(config_class=Config):
    """Creates and cinfigures the Flask application."""
    app = Flask(__name__)
    app.config.from_object(config_class)
    
    # Initialize extensions
    db.init_app(app)
    
    # Import and register blueprints
    from app.routes import bp as main_blueprint
    app.register_blueprint(main_blueprint)
    
    return app