from flask import Flask
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
import os

# Initialize extensions
db = SQLAlchemy()
migrate = Migrate()
login_manager = LoginManager()
login_manager.login_view = 'auth.login'  # Update this to your login route if different

def create_app():
    app = Flask(__name__)
    
    # Configuration
    app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', 'sqlite:///' + os.path.join(os.path.dirname(__file__), '..', 'app.db'))
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'your-secret-key-here')
    app.config['UPLOAD_FOLDER'] = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'uploads')
    
    # Ensure upload folder exists
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    
    # Initialize extensions with app
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    
    # Configure CORS with credentials support
    CORS(
        app,
        supports_credentials=True,
        origins=["http://localhost:3000"]
    )
    
    # Register blueprints and routes
    from .routes import init_app as init_routes
    init_routes(app)
    
    # Import models after db initialization to avoid circular imports
    with app.app_context():
        from . import models
    
    # Add CORS headers to every response
    @app.after_request
    def add_cors_headers(response):
        response.headers["Access-Control-Allow-Credentials"] = "true"
        response.headers["Access-Control-Allow-Origin"] = "http://localhost:3000"
        response.headers["Access-Control-Allow-Headers"] = "Content-Type, Authorization"
        response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, OPTIONS"
        return response
        
    # Handle preflight requests
    @app.route("/api/<path:path>", methods=["OPTIONS"])
    def options_handler(path):
        return "", 200
    
    # Import models here to avoid circular imports
    from . import models
    
    # Initialize database
    with app.app_context():
        try:
            db.create_all()  # This will create tables if they don't exist
            print("Database tables created successfully")
        except Exception as e:
            print(f"Error creating database tables: {str(e)}")
    
    # Register blueprints
    from .routes import init_app as init_routes
    init_routes(app)
    
    return app
