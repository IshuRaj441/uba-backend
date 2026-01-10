"""
API Routes for Universal Business Automation Dashboard
"""
import os
import uuid
import subprocess
from datetime import datetime
from flask import Blueprint, jsonify, request, send_file, current_app
from werkzeug.utils import secure_filename

# Create blueprint
api_bp = Blueprint('api', __name__)

def allowed_file(filename):
    """Check if the file has an allowed extension"""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in current_app.config['ALLOWED_EXTENSIONS']

@api_bp.route('/')
def api_root():
    """Root API endpoint with documentation"""
    return jsonify({
        'status': 'running',
        'version': '1.0.0',
        'message': 'Welcome to the Universal Business Automation API',
        'endpoints': {
            'health': '/api/health',
            'status': '/api/status',
            'leads': '/api/leads',
            'tools': '/api/tools',
            'convert': '/api/convert',
            'download': '/api/download/<file_id>'
        },
        'documentation': 'https://docs.universalbizautomat.com/api'
    })

@api_bp.route('/health')
def health():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.utcnow().isoformat(),
        'version': '1.0.0',
        'services': {
            'database': 'connected',
            'filesystem': 'operational',
            'conversion_tools': 'available'
        }
    })

@api_bp.route('/status')
def status():
    """System status endpoint"""
    return jsonify({
        'status': 'online',
        'last_checked': datetime.utcnow().isoformat(),
        'system': {
            'upload_dir': os.path.abspath(current_app.config['UPLOAD_FOLDER']),
            'output_dir': os.path.abspath(current_app.config['OUTPUT_FOLDER']),
            'max_upload_size': f"{current_app.config['MAX_CONTENT_LENGTH'] / (1024 * 1024)}MB"
        }
    })

@api_bp.route('/leads')
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
            'created_at': '2025-01-10T10:30:00Z'
        },
        {
            'id': 2,
            'name': 'Jane Smith',
            'email': 'jane@example.com',
            'company': 'Globex Corp',
            'status': 'contacted',
            'created_at': '2025-01-09T14:15:00Z'
        },
        {
            'id': 3,
            'name': 'Bob Johnson',
            'email': 'bob@example.com',
            'company': 'Initech',
            'status': 'qualified',
            'created_at': '2025-01-08T09:45:00Z'
        }
    ])

@api_bp.route('/tools')
def get_tools():
    """Get available conversion tools"""
    return jsonify({
        'tools': [
            {
                'id': 'pdf_to_word',
                'name': 'PDF to Word',
                'description': 'Convert PDF documents to editable Word format',
                'input': ['pdf'],
                'output': 'docx',
                'enabled': True
            },
            {
                'id': 'word_to_pdf',
                'name': 'Word to PDF',
                'description': 'Convert Word documents to PDF format',
                'input': ['doc', 'docx'],
                'output': 'pdf',
                'enabled': True
            },
            {
                'id': 'pdf_to_jpeg',
                'name': 'PDF to JPEG',
                'description': 'Convert PDF pages to JPEG images',
                'input': ['pdf'],
                'output': 'jpeg',
                'enabled': True
            },
            {
                'id': 'pdf_to_latex',
                'name': 'PDF to LaTeX',
                'description': 'Convert PDF documents to LaTeX source',
                'input': ['pdf'],
                'output': 'tex',
                'enabled': True
            },
            {
                'id': 'latex_to_pdf',
                'name': 'LaTeX to PDF',
                'description': 'Compile LaTeX documents to PDF',
                'input': ['tex'],
                'output': 'pdf',
                'enabled': True
            }
        ]
    })

@api_bp.route('/convert', methods=['POST'])
def convert():
    """Handle file conversion requests"""
    # Check if the post request has the file part
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400
    
    file = request.files['file']
    action = request.form.get('action')
    
    # If user does not select file, browser also
    # submit an empty part without filename
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400
    
    if not action:
        return jsonify({'error': 'No action specified'}), 400
    
    if file and allowed_file(file.filename):
        # Generate unique filename
        file_ext = file.filename.rsplit('.', 1)[1].lower()
        file_id = str(uuid.uuid4())
        filename = f"{file_id}.{file_ext}"
        
        # Save uploaded file
        upload_path = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
        file.save(upload_path)
        
        # Prepare output path
        output_filename = f"{file_id}"
        output_path = os.path.join(current_app.config['OUTPUT_FOLDER'], output_filename)
        
        try:
            # Perform conversion based on action
            if action == 'pdf_to_word':
                subprocess.run([
                    'soffice', '--headless', '--convert-to', 'docx',
                    '--outdir', current_app.config['OUTPUT_FOLDER'],
                    upload_path
                ], check=True)
                output_filename += '.docx'
                
            elif action == 'word_to_pdf':
                subprocess.run([
                    'soffice', '--headless', '--convert-to', 'pdf',
                    '--outdir', current_app.config['OUTPUT_FOLDER'],
                    upload_path
                ], check=True)
                output_filename += '.pdf'
                
            elif action == 'pdf_to_jpeg':
                subprocess.run([
                    'convert', '-density', '300',
                    upload_path,
                    os.path.join(current_app.config['OUTPUT_FOLDER'], f"{file_id}.jpg")
                ], check=True)
                output_filename += '.jpg'
                
            elif action == 'pdf_to_latex':
                subprocess.run([
                    'pandoc', upload_path, '-o', f"{output_path}.tex"
                ], check=True)
                output_filename += '.tex'
                
            elif action == 'latex_to_pdf':
                subprocess.run([
                    'pdflatex', '-output-directory', current_app.config['OUTPUT_FOLDER'],
                    upload_path
                ], check=True)
                output_filename += '.pdf'
                
            else:
                return jsonify({'error': 'Invalid action'}), 400
                
            return jsonify({
                'success': True,
                'message': 'Conversion successful',
                'file_id': file_id,
                'download_url': f"/api/download/{output_filename}"
            })
            
        except subprocess.CalledProcessError as e:
            current_app.logger.error(f"Conversion failed: {str(e)}")
            return jsonify({
                'error': 'Conversion failed',
                'details': str(e)
            }), 500
            
        except Exception as e:
            current_app.logger.error(f"Unexpected error: {str(e)}")
            return jsonify({
                'error': 'An unexpected error occurred',
                'details': str(e)
            }), 500
            
    return jsonify({'error': 'File type not allowed'}), 400

@api_bp.route('/download/<path:filename>')
def download_file(filename):
    """Download converted files"""
    # Sanitize filename to prevent directory traversal
    safe_filename = secure_filename(filename)
    file_path = os.path.join(current_app.config['OUTPUT_FOLDER'], safe_filename)
    
    if not os.path.exists(file_path):
        return jsonify({'error': 'File not found'}), 404
        
    return send_file(
        file_path,
        as_attachment=True,
        download_name=safe_filename
    )
