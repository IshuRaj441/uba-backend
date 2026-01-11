import os
import uuid
import subprocess
import time
from datetime import datetime, timedelta
from flask import Flask, jsonify, request, send_file, send_from_directory, url_for
from flask_cors import CORS
from extensions import db, migrate
from werkzeug.security import generate_password_hash, check_password_hash
from routes.auth_routes import auth_bp
from routes.api_routes import api_bp
from werkzeug.utils import secure_filename
from functools import wraps
import jwt

# Initialize extensions
db = db
migrate = migrate

def create_app():
    # Configuration
    UPLOAD_FOLDER = 'uploads'
    OUTPUT_FOLDER = 'outputs'
    ALLOWED_EXTENSIONS = {'pdf', 'docx', 'doc', 'tex', 'jpg', 'jpeg', 'png'}
    
    # JWT Configuration
    JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY', 'dev-key-change-in-production-123')
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(days=30)
    
    # Set secret key for session and JWT
    app = Flask(__name__)
    app.secret_key = JWT_SECRET_KEY

    # Ensure directories exist
    BASE_DIR = os.path.abspath(os.path.dirname(__file__))
    
    # Create data directory for database with proper permissions
    DATA_DIR = os.path.abspath(os.path.join(BASE_DIR, 'data'))
    os.makedirs(DATA_DIR, exist_ok=True)
    
    # Set full permissions on the data directory (Windows)
    try:
        import stat
        os.chmod(DATA_DIR, stat.S_IRWXU | stat.S_IRWXG | stat.S_IRWXO)
    except Exception as e:
        print(f"Warning: Could not set permissions on {DATA_DIR}: {e}")
    
    # Create other required directories
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)
    os.makedirs(OUTPUT_FOLDER, exist_ok=True)

    # Register blueprints
    app.register_blueprint(auth_bp, url_prefix='/api/auth')
    app.register_blueprint(api_bp, url_prefix='/api')

    # Get the absolute path to the frontend build directory
    frontend_build_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'frontend', 'build'))

    app = Flask(__name__, static_folder=frontend_build_path, static_url_path='')
    
    # App config
    app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
    app.config['OUTPUT_FOLDER'] = OUTPUT_FOLDER
    app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-key-change-in-production')
    app.config['JWT_SECRET_KEY'] = JWT_SECRET_KEY
    
    # Use file-based SQLite database
    db_path = os.path.join('instance', 'app.db')
    os.makedirs('instance', exist_ok=True)
    db_uri = f'sqlite:///{os.path.abspath(db_path)}'
    app.config['SQLALCHEMY_DATABASE_URI'] = db_uri
    app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
        'connect_args': {
            'timeout': 30,  # seconds
            'check_same_thread': False
        }
    }
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    print(f"Using SQLite database at: {db_path}")
    
    # Initialize extensions
    db.init_app(app)
    migrate.init_app(app, db)

    # Configure CORS
    CORS(app, 
        resources={"*": {"origins": ["http://localhost:3000", "http://localhost:3003"]}},
        supports_credentials=True,
        allow_headers=["Content-Type", "Authorization", "X-Requested-With"],
        methods=["GET", "HEAD", "POST", "OPTIONS", "PUT", "PATCH", "DELETE"],
        expose_headers=["Content-Disposition"]
    )
    
    # Import and register blueprints
    from routes import api_routes, auth_routes
    app.register_blueprint(api_routes.api_bp, url_prefix='/api')
    app.register_blueprint(auth_routes.auth_bp, url_prefix='/api/auth')
    
    # Import models
    from models.user import User
    
    # Create database tables
    with app.app_context():
        db.create_all()
        
        # Create admin user if not exists
        if not User.query.filter_by(email='admin@example.com').first():
            admin = User(
                email='admin@example.com',
                password=generate_password_hash('admin123'),
                credits=1000,
                is_admin=True
            )
            db.session.add(admin)
            db.session.commit()
        
        # Create test user if not exists
        test_email = 'raji53681@gmail.com'
        if not User.query.filter_by(email=test_email).first():
            test_user = User(
                email=test_email,
                password=generate_password_hash('test123'),  # You can change this password
                credits=100,
                is_admin=False
            )
            db.session.add(test_user)
            db.session.commit()
            print(f"Created test user with email: {test_email}")

    # Application start time
    app.start_time = time.time()

    # Helper functions
    def allowed_file(filename):
        return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

    def get_system_info():
        """Get system information including installed tools"""
        tools = {
            'libreoffice': False,
            'pandoc': False,
            'imagemagick': False,
            'pdflatex': False,
            'poppler': False
        }
        try:
            subprocess.run(['soffice', '--version'], stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
            tools['libreoffice'] = True
        except:
            pass

        try:
            subprocess.run(['pandoc', '--version'], stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
            tools['pandoc'] = True
        except:
            pass

        try:
            subprocess.run(['convert', '--version'], stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
            tools['imagemagick'] = True
        except:
            pass

        try:
            subprocess.run(['pdflatex', '--version'], stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
            tools['pdflatex'] = True
        except:
            pass

        try:
            subprocess.run(['pdftoppm', '-v'], stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
            tools['poppler'] = True
        except:
            pass

        return tools

    # Routes
    @app.route('/')
    def serve():
        return app.send_static_file('index.html')

    @app.route('/api')
    def root():
        """Root API endpoint with service information"""
        return jsonify({
            'service': 'Universal Business Automator API',
            'version': '1.0.0',
            'status': 'operational',
            'endpoints': {
                'health': '/api/health',
                'status': '/api/status',
                'leads': '/api/leads',
                'tools': '/api/tools',
                'convert': '/api/convert'
            },
            'documentation': 'https://github.com/yourusername/uba-backend'
        })

    @app.route('/api/health')
    def health():
        """Health check endpoint"""
        return jsonify({
            'status': 'healthy',
            'timestamp': datetime.utcnow().isoformat(),
            'uptime': round(time.time() - app.start_time, 2)
        })

    @app.route('/api/status')
    def status():
        """System status endpoint"""
        system_info = get_system_info()
        return jsonify({
            'status': 'operational' if all(system_info.values()) else 'degraded',
            'timestamp': datetime.utcnow().isoformat(),
            'system': {
                'tools': system_info,
                'missing_tools': [k for k, v in system_info.items() if not v]
            }
        })

    @app.route('/api/leads')
    def get_leads():
        """Get sample leads data"""
        return jsonify({
            'leads': [
                {
                    'id': 1,
                    'name': 'John Doe',
                    'email': 'john@example.com',
                    'company': 'Acme Inc',
                    'status': 'new',
                    'created_at': '2023-06-15T10:30:00Z'
                },
                {
                    'id': 2,
                    'name': 'Jane Smith',
                    'email': 'jane@example.com',
                    'company': 'Tech Corp',
                    'status': 'contacted',
                    'created_at': '2023-06-14T15:45:00Z'
                }
            ]
        })

    @app.route('/api/tools')
    def get_tools():
        """Get available conversion tools"""
        return jsonify({
            'tools': [
                {
                    'id': 'pdf_to_word',
                    'name': 'PDF to Word',
                    'description': 'Convert PDF documents to editable Word format',
                    'input_formats': ['pdf'],
                    'output_format': 'docx',
                    'enabled': True
                },
                {
                    'id': 'word_to_pdf',
                    'name': 'Word to PDF',
                    'description': 'Convert Word documents to PDF format',
                    'input_formats': ['docx', 'doc'],
                    'output_format': 'pdf',
                    'enabled': True
                }
            ]
        })

    @app.route('/api/convert', methods=['POST'])
    def convert():
        """Handle file conversion"""
        if 'file' not in request.files:
            return jsonify({'error': 'No file part'}), 400
            
        file = request.files['file']
        
        if file.filename == '':
            return jsonify({'error': 'No selected file'}), 400
            
        action = request.form.get('action')
        if not action:
            return jsonify({'error': 'No action specified'}), 400
        
        if not allowed_file(file.filename):
            return jsonify({'error': 'File type not allowed'}), 400
        
        uid = str(uuid.uuid4())
        filename = secure_filename(file.filename)
        base_name = os.path.splitext(filename)[0]
        
        in_path = os.path.join(app.config['UPLOAD_FOLDER'], f"{uid}_{filename}")
        file.save(in_path)
        
        try:
            output_ext = ''
            out_filename = f"{uid}_{base_name}"
            
            if action == 'pdf_to_word':
                output_ext = '.docx'
                out_path = os.path.join(app.config['OUTPUT_FOLDER'], f"{out_filename}{output_ext}")
                subprocess.run([
                    'soffice', '--headless', '--convert-to', 'docx',
                    '--outdir', app.config['OUTPUT_FOLDER'], in_path
                ], check=True)
                
            elif action == 'word_to_pdf':
                output_ext = '.pdf'
                out_path = os.path.join(app.config['OUTPUT_FOLDER'], f"{out_filename}{output_ext}")
                subprocess.run([
                    'soffice', '--headless', '--convert-to', 'pdf',
                    '--outdir', app.config['OUTPUT_FOLDER'], in_path
                ], check=True)
            else:
                os.remove(in_path)
                return jsonify({'error': 'Invalid action'}), 400
                
            return jsonify({
                'success': True,
                'download_url': f'/api/download/{uid}',
                'filename': f"{base_name}{output_ext}",
                'action': action,
                'timestamp': datetime.utcnow().isoformat()
            })
            
        except subprocess.CalledProcessError as e:
            if os.path.exists(in_path):
                os.remove(in_path)
            return jsonify({
                'error': f'Conversion failed: {str(e)}',
                'details': str(e.stderr) if hasattr(e, 'stderr') else 'No details available'
            }), 500
            
        except Exception as e:
            if os.path.exists(in_path):
                os.remove(in_path)
            return jsonify({
                'error': f'An unexpected error occurred: {str(e)}'
            }), 500

    @app.route('/api/download/<uid>')
    def download(uid):
        """Download converted files"""
        output_dir = app.config['OUTPUT_FOLDER']
        
        for filename in os.listdir(output_dir):
            if filename.startswith(uid):
                file_path = os.path.join(output_dir, filename)
                
                def cleanup():
                    try:
                        os.remove(file_path)
                    except:
                        pass
                        
                response = send_file(file_path, as_attachment=True)
                response.call_on_close(cleanup)
                return response
                
        return jsonify({'error': 'File not found or has expired'}), 404

    # Error handlers
    @app.errorhandler(404)
    def not_found_error(error):
        return jsonify({'error': 'Not found'}), 404

    @app.errorhandler(500)
    def internal_error(error):
        return jsonify({'error': 'Internal server error'}), 500

    return app

# For development
if __name__ == '__main__':
    app = create_app()
    # Run the application
    app.run(debug=True, host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))