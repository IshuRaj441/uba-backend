import os
import uuid
import subprocess
import time
from datetime import datetime
from flask import Flask, jsonify, request, send_file, send_from_directory
from flask_cors import CORS
from werkzeug.utils import secure_filename

# Configuration
UPLOAD_FOLDER = 'uploads'
OUTPUT_FOLDER = 'outputs'
ALLOWED_EXTENSIONS = {'pdf', 'docx', 'doc', 'tex', 'jpg', 'jpeg', 'png'}

# Ensure upload and output directories exist
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

import os

# Get the absolute path to the frontend build directory
frontend_build_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'frontend', 'build'))

app = Flask(__name__, static_folder=frontend_build_path, static_url_path='')
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['OUTPUT_FOLDER'] = OUTPUT_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

# Configure CORS
CORS(app, 
     resources={"*": {"origins": ["http://localhost:3000", "http://localhost:3003"]}},
     supports_credentials=True,
     allow_headers=["Content-Type", "Authorization", "X-Requested-With"],
     methods=["GET", "HEAD", "POST", "OPTIONS", "PUT", "PATCH", "DELETE"],
     expose_headers=["Content-Disposition"])

# Application start time
START_TIME = time.time()

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
    except (subprocess.SubprocessError, FileNotFoundError):
        pass
        
    try:
        subprocess.run(['pandoc', '--version'], stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
        tools['pandoc'] = True
    except (subprocess.SubprocessError, FileNotFoundError):
        pass
        
    try:
        subprocess.run(['convert', '--version'], stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
        tools['imagemagick'] = True
    except (subprocess.SubprocessError, FileNotFoundError):
        pass
        
    try:
        subprocess.run(['pdflatex', '--version'], stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
        tools['pdflatex'] = True
    except (subprocess.SubprocessError, FileNotFoundError):
        pass
        
    try:
        subprocess.run(['pdftoppm', '-v'], stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
        tools['poppler'] = True
    except (subprocess.SubprocessError, FileNotFoundError):
        pass
        
    return tools

# Routes
@app.route('/')
def serve():
    return send_from_directory(app.static_folder, 'index.html')

@app.route('/api')
def root():
    """Root API endpoint with service information"""
    return jsonify({
        'status': 'running',
        'version': '1.0.0',
        'message': 'Welcome to the Universal Business Automation API',
        'timestamp': datetime.utcnow().isoformat(),
        'endpoints': {
            'health': '/api/health',
            'status': '/api/status',
            'leads': '/api/leads',
            'tools': '/api/tools',
            'convert': '/api/convert',
            'documentation': 'https://docs.example.com/api'
        }
    })

@app.route('/api/health')
def health():
    """Health check endpoint"""
    current_time = time.time()
    uptime = str(datetime.utcfromtimestamp(current_time - START_TIME).strftime('%H:%M:%S'))
    
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.utcnow().isoformat(),
        'uptime': uptime,
        'system': {
            'platform': os.name,
            'python_version': '.'.join(map(str, os.sys.version_info[:3]))
        },
        'dependencies': get_system_info()
    })

@app.route('/api/status')
def status():
    """System status endpoint"""
    return jsonify({
        'status': 'operational',
        'timestamp': datetime.utcnow().isoformat(),
        'services': {
            'api': 'online',
            'database': 'online',
            'file_processing': 'online',
            'conversion_engine': 'online'
        },
        'resources': {
            'cpu_usage': '25%',  # This would be dynamic in production
            'memory_usage': '45%',
            'disk_space': '1.2TB/2TB'
        },
        'last_checked': datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')
    })

@app.route('/api/leads')
def get_leads():
    """Get sample leads data"""
    # In a real app, this would come from a database
    return jsonify([
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
        },
        {
            'id': 3,
            'name': 'Bob Johnson',
            'email': 'bob@example.com',
            'company': 'Innovate LLC',
            'status': 'qualified',
            'created_at': '2023-06-10T09:15:00Z'
        }
    ])

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
            },
            {
                'id': 'pdf_to_jpeg',
                'name': 'PDF to JPEG',
                'description': 'Convert PDF pages to JPEG images',
                'input_formats': ['pdf'],
                'output_format': 'jpg',
                'enabled': True
            },
            {
                'id': 'pdf_to_latex',
                'name': 'PDF to LaTeX',
                'description': 'Convert PDF to LaTeX source',
                'input_formats': ['pdf'],
                'output_format': 'tex',
                'enabled': True
            },
            {
                'id': 'latex_to_pdf',
                'name': 'LaTeX to PDF',
                'description': 'Compile LaTeX source to PDF',
                'input_formats': ['tex'],
                'output_format': 'pdf',
                'enabled': True
            }
        ]
    })

@app.route('/api/convert', methods=['POST'])
def convert():
    """Handle file conversion"""
    # Check if the post request has the file part
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400
        
    file = request.files['file']
    
    # If user does not select file, browser also
    # submit an empty part without filename
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400
        
    # Get the action from the form data
    action = request.form.get('action')
    if not action:
        return jsonify({'error': 'No action specified'}), 400
    
    # Validate file extension
    if not allowed_file(file.filename):
        return jsonify({'error': 'File type not allowed'}), 400
    
    # Generate unique ID for this conversion
    uid = str(uuid.uuid4())
    filename = secure_filename(file.filename)
    base_name = os.path.splitext(filename)[0]
    
    # Save the uploaded file
    in_path = os.path.join(app.config['UPLOAD_FOLDER'], f"{uid}_{filename}")
    file.save(in_path)
    
    try:
        output_ext = ''
        out_filename = f"{uid}_{base_name}"
        
        # Handle different conversion types
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
            
        elif action == 'pdf_to_jpeg':
            output_ext = '.jpg'
            out_path = os.path.join(app.config['OUTPUT_FOLDER'], f"{out_filename}{output_ext}")
            subprocess.run([
                'convert', '-density', '300', in_path, 
                '-quality', '90', out_path
            ], check=True)
            
        elif action == 'pdf_to_latex':
            output_ext = '.tex'
            out_path = os.path.join(app.config['OUTPUT_FOLDER'], f"{out_filename}{output_ext}")
            subprocess.run([
                'pandoc', in_path, '-o', out_path, '--standalone'
            ], check=True)
            
        elif action == 'latex_to_pdf':
            output_ext = '.pdf'
            out_path = os.path.join(app.config['OUTPUT_FOLDER'], f"{out_filename}{output_ext}")
            # Run pdflatex twice to ensure references are resolved
            subprocess.run([
                'pdflatex', '-output-directory', app.config['OUTPUT_FOLDER'],
                '-interaction=nonstopmode', in_path
            ], check=True)
            subprocess.run([
                'pdflatex', '-output-directory', app.config['OUTPUT_FOLDER'],
                '-interaction=nonstopmode', in_path
            ], check=True)
            
            # Clean up aux and log files
            for ext in ['.aux', '.log', '.out']:
                aux_file = os.path.join(app.config['OUTPUT_FOLDER'], f"{os.path.splitext(filename)[0]}{ext}")
                if os.path.exists(aux_file):
                    os.remove(aux_file)
        else:
            os.remove(in_path)
            return jsonify({'error': 'Invalid action'}), 400
            
        # Return success response with download link
        return jsonify({
            'success': True,
            'download_url': f'/api/download/{uid}',
            'filename': f"{base_name}{output_ext}",
            'action': action,
            'timestamp': datetime.utcnow().isoformat()
        })
        
    except subprocess.CalledProcessError as e:
        # Clean up on error
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
    
    # Find the file with the matching UID
    for filename in os.listdir(output_dir):
        if filename.startswith(uid):
            file_path = os.path.join(output_dir, filename)
            
            # Clean up the file after sending (optional)
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

if __name__ == '__main__':
    # Check for required tools
    system_info = get_system_info()
    missing_tools = [tool for tool, available in system_info.items() if not available]
    
    if missing_tools:
        print("WARNING: The following tools are not installed or not in PATH:")
        for tool in missing_tools:
            print(f"- {tool}")
        print("\nPlease install them for full functionality.")
    
    # Start the application
    app.run(host='0.0.0.0', port=5000, debug=True)
