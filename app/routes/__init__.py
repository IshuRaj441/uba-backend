from flask import Blueprint, jsonify, current_app
from app import db
from app.models import Lead, Document, ConversionJob
from datetime import datetime
import os

# Create blueprints
bp = Blueprint('main', __name__)
api_bp = Blueprint('api', __name__, url_prefix='/api')

# Root route with API information
@bp.route('/')
def index():
    return jsonify({
        'status': 'running',
        'version': '1.0.0',
        'message': 'Welcome to the Universal Business Automation API',
        'endpoints': {
            'health': '/api/health',
            'status': '/api/status',
            'leads': '/api/leads',
            'pdfs': '/api/pdfs'
        }
    })

def init_app(app):
    # Import routes after creating blueprints to avoid circular imports
    from . import api_routes  # noqa
    
    # Register blueprints
    app.register_blueprint(bp)
    app.register_blueprint(api_routes.api_bp, url_prefix='/api')
    
    # Create upload directories if they don't exist
    os.makedirs(os.path.join(app.config['UPLOAD_FOLDER'], 'converted'), exist_ok=True)
    os.makedirs(os.path.join(app.config['UPLOAD_FOLDER'], 'uploads'), exist_ok=True)
    app.register_blueprint(leads_bp, url_prefix='/api/leads')
    app.register_blueprint(documents.bp, url_prefix='/api/documents')
    
    # Additional configuration
    # Ensure upload directory exists
    upload_dir = os.path.join(app.root_path, '..', 'uploads')
    os.makedirs(upload_dir, exist_ok=True)
    
    # Create a test route
    @app.route('/')
    def index():
        return 'Universal Business Automation API is running!'
    
    # Add CORS headers to all responses
    @app.after_request
    def add_cors_headers(response):
        response.headers.add('Access-Control-Allow-Origin', '*')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
        response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS')
        return response
