"""
Universal Business Automation Dashboard - Backend Package
"""
import os
from flask import Flask, jsonify, request
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from werkzeug.utils import secure_filename

# Initialize extensions
db = SQLAlchemy()

def create_app():
    """
    Application factory function to create and configure the Flask app.
    
    Returns:
        Flask: The configured Flask application instance.
    """
    app = Flask(__name__)
    
    # Configuration
    app.config.update(
        SECRET_KEY=os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production'),
        SQLALCHEMY_DATABASE_URI=os.getenv(
            'SQLALCHEMY_DATABASE_URI',
            'sqlite:///automation_dashboard.db'
        ),
        SQLALCHEMY_TRACK_MODIFICATIONS=False,
        UPLOAD_FOLDER=os.path.join(os.path.dirname(os.path.abspath(__file__)), 'uploads'),
        OUTPUT_FOLDER=os.path.join(os.path.dirname(os.path.abspath(__file__)), 'outputs'),
        MAX_CONTENT_LENGTH=16 * 1024 * 1024,  # 16MB max file size
        ALLOWED_EXTENSIONS={'pdf', 'doc', 'docx', 'tex', 'jpg', 'jpeg', 'png'}
    )
    
    # Ensure upload and output directories exist
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    os.makedirs(app.config['OUTPUT_FOLDER'], exist_ok=True)
    
    # Initialize extensions
    db.init_app(app)
    
    # Configure CORS
    CORS(app, 
         resources={"*": {"origins": ["http://localhost:3000", "http://localhost:3003"]}},
         supports_credentials=True,
         allow_headers=["Content-Type", "Authorization", "X-Requested-With"],
         methods=["GET", "HEAD", "POST", "OPTIONS", "PUT", "PATCH", "DELETE"],
         expose_headers=["Content-Disposition"])
    
    # Register routes
    from .routes import init_app as init_routes
    init_routes(app)
    
    # Register API blueprint
    from .routes.api_routes import api_bp
    app.register_blueprint(api_bp, url_prefix='/api')
    
    # Import models to ensure they are registered with SQLAlchemy
    from . import models
    
    # Create database tables
    with app.app_context():
        db.create_all()
    
    return app