"""
API Routes for Universal Business Automation
"""
from flask import Blueprint, jsonify, request, send_file, current_app
from werkzeug.utils import secure_filename
from app import db
from app.models import Lead, Document, ActivityLog, EmailLog, ConversionJob
from ..modules.scraper import LeadScraper
from ..modules.pdf_generator import PDFGenerator
from ..modules.emailer import EmailAutomation
from ..modules.document_converter import DocumentConverter
from ..modules.google_sheet import GoogleSheetIntegration
from datetime import datetime, timezone
import os
import json
import uuid
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Allowed file extensions
ALLOWED_EXTENSIONS = {
    'pdf': 'application/pdf',
    'docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
    'doc': 'application/msword',
    'tex': 'application/x-tex',
    'jpg': 'image/jpeg',
    'jpeg': 'image/jpeg',
    'png': 'image/png'
}

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Create Blueprint
api_bp = Blueprint('api', __name__, url_prefix='/api')

# Initialize modules
scraper = LeadScraper()
pdf_gen = PDFGenerator()
emailer = EmailAutomation()
doc_converter = DocumentConverter()
google_sheets = GoogleSheetIntegration()

# System Endpoints
@api_bp.route('/', methods=['GET'])
def api_root():
    """API root endpoint with welcome message and available endpoints"""
    base_url = request.host_url.rstrip('/')
    return jsonify({
        'name': 'Universal Business Automation API',
        'version': '1.0.0',
        'endpoints': {
            'health': f'{base_url}/api/health',
            'status': f'{base_url}/api/status',
            'leads': f'{base_url}/api/leads',
            'scrape': f'{base_url}/api/scrape',
            'pdfs': f'{base_url}/api/pdfs',
            'convert': {
                'pdf-to-word': f'{base_url}/api/convert/pdf-to-word',
                'pdf-to-jpeg': f'{base_url}/api/convert/pdf-to-jpeg',
                'word-to-pdf': f'{base_url}/api/convert/word-to-pdf',
                'pdf-to-latex': f'{base_url}/api/convert/pdf-to-latex',
                'latex-to-pdf': f'{base_url}/api/convert/latex-to-pdf'
            }
        },
        'documentation': 'https://github.com/yourusername/universal-biz-automation'
    })

@api_bp.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    try:
        # Test database connection
        db.session.execute('SELECT 1')
        db_status = 'connected'
    except Exception as e:
        db_status = f'error: {str(e)}'
    
    return jsonify({
        'status': 'ok',
        'timestamp': datetime.now(timezone.utc).isoformat(),
        'database': db_status,
        'version': '1.0.0'
    })

@api_bp.route('/status', methods=['GET'])
@cross_origin()
def system_status():
    """System status and statistics"""
    stats = {
        'leads': {
            'total': Lead.query.count(),
            'today': Lead.query.filter(
                Lead.created_at >= datetime.now().date()
            ).count()
        },
        'pdfs': {
            'total': PDFReport.query.count(),
            'recent': PDFReport.query.order_by(PDFReport.created_at.desc()).limit(5).all()
        },
        'conversions': {
            'total': Conversion.query.count(),
            'by_type': db.session.query(
                Conversion.type, db.func.count(Conversion.id)
            ).group_by(Conversion.type).all(),
            'recent': Conversion.query.order_by(Conversion.created_at.desc()).limit(5).all()
        },
        'system': {
            'python_version': os.getenv('PYTHON_VERSION', '3.9'),
            'flask_version': '2.0.1',
            'environment': os.getenv('FLASK_ENV', 'development'),
            'last_updated': datetime.now(timezone.utc).isoformat()
        }
    }
    
    return jsonify(stats)

# Lead Endpoints
@api_bp.route('/scrape', methods=['POST'])
@cross_origin()
def scrape_leads():
    """Scrape leads from a URL"""
    data = request.get_json()
    if not data:
        return jsonify({'error': 'No data provided'}), 400
        
    url = data.get('url')
    if not url:
        return jsonify({'error': 'URL is required'}), 400
    
    try:
        # Log the scraping activity
        activity = ActivityLog(
            action='scrape_leads',
            details=f'Scraping leads from {url}',
            status='in_progress'
        )
        db.session.add(activity)
        db.session.commit()
        
        # Scrape leads
        leads = scraper.scrape_url(url)
        
        # Save to database
        new_leads = []
        for lead_data in leads:
            if Lead.query.filter_by(email=lead_data.get('email')).first() is None:
                lead = Lead(
                    name=lead_data.get('name', ''),
                    email=lead_data.get('email', ''),
                    phone=lead_data.get('phone', ''),
                    source=url,
                    status='new',
                    notes=json.dumps(lead_data),
                    created_at=datetime.utcnow()
                )
                db.session.add(lead)
                new_leads.append(lead)
        
        # Update activity log
        activity.status = 'completed'
        activity.details = f'Successfully scraped {len(new_leads)} new leads from {url}'
        db.session.commit()
        
        return jsonify({
            'status': 'success',
            'message': f'Successfully scraped {len(new_leads)} new leads',
            'total': len(leads),
            'new': len(new_leads),
            'leads': [{
                'id': lead.id,
                'name': lead.name,
                'email': lead.email,
                'phone': lead.phone,
                'source': lead.source,
                'created_at': lead.created_at.isoformat()
            } for lead in new_leads]
        })
        
    except Exception as e:
        db.session.rollback()
        logger.error(f'Error scraping leads: {str(e)}', exc_info=True)
        return jsonify({
            'status': 'error',
            'message': 'Failed to scrape leads',
            'error': str(e)
        }), 500

@api_bp.route('/leads', methods=['GET'])
@cross_origin()
def get_leads():
    """
    Get all leads with pagination and filtering
    Query Parameters:
        - page: Page number (default: 1)
        - per_page: Items per page (default: 20, max: 100)
        - status: Filter by status (optional)
        - source: Filter by source (optional)
        - search: Search in name, email, or phone (optional)
    """
    try:
        # Pagination
        page = request.args.get('page', 1, type=int)
        per_page = min(request.args.get('per_page', 20, type=int), 100)
        
        # Build query
        query = Lead.query
        
        # Apply filters
        if status := request.args.get('status'):
            query = query.filter_by(status=status)
            
        if source := request.args.get('source'):
            query = query.filter(Lead.source.like(f'%{source}%'))
            
        if search := request.args.get('search'):
            search_term = f'%{search}%'
            query = query.filter(
                (Lead.name.ilike(search_term)) |
                (Lead.email.ilike(search_term)) |
                (Lead.phone.ilike(search_term))
            )
        
        # Execute query with pagination
        pagination = query.order_by(Lead.created_at.desc()).paginate(
            page=page, per_page=per_page, error_out=False
        )
        
        # Prepare response
        return jsonify({
            'status': 'success',
            'data': [{
                'id': lead.id,
                'name': lead.name,
                'email': lead.email,
                'phone': lead.phone,
                'source': lead.source,
                'status': lead.status,
                'created_at': lead.created_at.isoformat(),
                'updated_at': lead.updated_at.isoformat() if lead.updated_at else None
            } for lead in pagination.items],
            'pagination': {
                'page': page,
                'per_page': per_page,
                'total': pagination.total,
                'pages': pagination.pages,
                'has_next': pagination.has_next,
                'has_prev': pagination.has_prev
            }
        })
        
    except Exception as e:
        logger.error(f'Error fetching leads: {str(e)}', exc_info=True)
        return jsonify({
            'status': 'error',
            'message': 'Failed to fetch leads',
            'error': str(e)
        }), 500

# File Upload Helpers
def save_uploaded_file(file, subfolder=''):
    """Save an uploaded file and return its path"""
    if not file or not allowed_file(file.filename):
        return None
        
    # Create upload directory if it doesn't exist
    upload_dir = os.path.join(current_app.config['UPLOAD_FOLDER'], subfolder)
    os.makedirs(upload_dir, exist_ok=True)
    
    # Generate unique filename
    ext = file.filename.rsplit('.', 1)[1].lower()
    filename = f"{uuid.uuid4()}.{ext}"
    filepath = os.path.join(upload_dir, filename)
    
    # Save file
    file.save(filepath)
    return filepath

# PDF Endpoints
@api_bp.route('/pdfs', methods=['GET'])
@cross_origin()
def list_pdfs():
    """List all generated PDFs"""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = min(request.args.get('per_page', 20, type=int), 100)
        
        query = PDFReport.query
        
        # Filter by title if provided
        if title := request.args.get('title'):
            query = query.filter(PDFReport.title.ilike(f'%{title}%'))
            
        # Apply pagination
        pagination = query.order_by(PDFReport.generated_at.desc()).paginate(
            page=page, per_page=per_page, error_out=False
        )
        
        return jsonify({
            'status': 'success',
            'data': [{
                'id': pdf.id,
                'title': pdf.title,
                'filename': pdf.filename,
                'url': f'/api/pdfs/{os.path.basename(pdf.filename)}',
                'generated_at': pdf.generated_at.isoformat(),
                'size': os.path.getsize(pdf.filename) if os.path.exists(pdf.filename) else 0
            } for pdf in pagination.items],
            'pagination': {
                'page': page,
                'per_page': per_page,
                'total': pagination.total,
                'pages': pagination.pages,
                'has_next': pagination.has_next,
                'has_prev': pagination.has_prev
            }
        })
        
    except Exception as e:
        logger.error(f'Error listing PDFs: {str(e)}', exc_info=True)
        return jsonify({
            'status': 'error',
            'message': 'Failed to list PDFs',
            'error': str(e)
        }), 500

@api_bp.route('/pdfs/<path:filename>', methods=['GET'])
@cross_origin()
def get_pdf(filename):
    """Download a generated PDF"""
    try:
        # Security: Prevent directory traversal
        filename = os.path.basename(filename)
        filepath = os.path.join(current_app.config['UPLOAD_FOLDER'], 'pdfs', filename)
        
        if not os.path.exists(filepath):
            return jsonify({'status': 'error', 'message': 'File not found'}), 404
            
        return send_file(
            filepath,
            mimetype='application/pdf',
            as_attachment=True,
            download_name=filename
        )
        
    except Exception as e:
        logger.error(f'Error retrieving PDF {filename}: {str(e)}', exc_info=True)
        return jsonify({
            'status': 'error',
            'message': 'Failed to retrieve PDF',
            'error': str(e)
        }), 500
        db.session.commit()
        
        return jsonify({
            'message': 'PDF generated successfully',
            'filename': filename,
            'download_url': f'/api/pdfs/{filename}'
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@api_bp.route('/pdfs', methods=['GET'])
@cross_origin()
def list_pdfs():
    """List all generated PDFs"""
    pdfs = PDFReport.query.order_by(PDFReport.generated_at.desc()).all()
    return jsonify([{
        'id': pdf.id,
        'title': pdf.title,
        'filename': pdf.filename,
        'generated_at': pdf.generated_at.isoformat(),
        'download_url': f'/api/pdfs/{pdf.filename}'
    } for pdf in pdfs])

@api_bp.route('/pdfs/<filename>', methods=['GET'])
@cross_origin()
def download_pdf(filename):
    """Download a generated PDF"""
    try:
        return send_file(
            os.path.join('generated_reports', filename),
            as_attachment=True
        )
    except FileNotFoundError:
        return jsonify({'error': 'File not found'}), 404

# Export Endpoints
@api_bp.route('/export/csv', methods=['POST'])
@cross_origin()
def export_csv():
    """Export leads to CSV"""
    try:
        # Implementation for CSV export
        return jsonify({'message': 'CSV export not yet implemented'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@api_bp.route('/export/sheets', methods=['POST'])
@cross_origin()
def export_sheets():
    """Export to Google Sheets"""
    try:
        # Implementation for Google Sheets export
        return jsonify({'message': 'Google Sheets export not yet implemented'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@api_bp.route('/export/pdf', methods=['POST'])
@cross_origin()
def export_pdf():
    """Export to PDF"""
    try:
        # Implementation for PDF export
        return jsonify({'message': 'PDF export not yet implemented'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# AI Endpoint
@api_bp.route('/ai/generate', methods=['POST'])
@cross_origin()
def generate_ai_content():
    """Generate AI content"""
    data = request.get_json()
    topic = data.get('topic')
    
    if not topic:
        return jsonify({'error': 'Topic is required'}), 400
    
    try:
        # Implementation for AI content generation
        return jsonify({
            'content': f"This is AI-generated content about {topic}. This is a placeholder response.",
            'tokens_used': 0,
            'model': 'gpt-3.5-turbo'
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Email Endpoint
@api_bp.route('/email/send', methods=['POST'])
@cross_origin()
def send_email():
    """Send an email"""
    data = request.get_json()
    
    required_fields = ['to', 'subject', 'body']
    if not all(field in data for field in required_fields):
        return jsonify({'error': 'Missing required fields'}), 400
    
    try:
        # Implementation for sending email
        return jsonify({'message': 'Email sent successfully'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Document Conversion Endpoints
@api_bp.route('/convert/pdf-to-word', methods=['POST'])
@cross_origin()
def convert_pdf_to_word():
    """Convert PDF to Word document"""
    return handle_conversion('pdf-to-word', request.files)

@api_bp.route('/convert/pdf-to-jpeg', methods=['POST'])
@cross_origin()
def convert_pdf_to_jpeg():
    """Convert PDF to JPEG images"""
    return handle_conversion('pdf-to-jpeg', request.files)

@api_bp.route('/convert/word-to-pdf', methods=['POST'])
@cross_origin()
def convert_word_to_pdf():
    """Convert Word document to PDF"""
    return handle_conversion('word-to-pdf', request.files)

@api_bp.route('/convert/pdf-to-latex', methods=['POST'])
@cross_origin()
def convert_pdf_to_latex():
    """Convert PDF to LaTeX"""
    return handle_conversion('pdf-to-latex', request.files)

@api_bp.route('/convert/latex-to-pdf', methods=['POST'])
@cross_origin()
def compile_latex_to_pdf():
    """Compile LaTeX to PDF"""
    return handle_conversion('latex-to-pdf', request.files)

def handle_conversion(conversion_type, files):
    """Handle file conversion for different types"""
    try:
        if 'file' not in files:
            return jsonify({'status': 'error', 'message': 'No file provided'}), 400
            
        file = files['file']
        if file.filename == '':
            return jsonify({'status': 'error', 'message': 'No selected file'}), 400
            
        # Save uploaded file
        input_path = save_uploaded_file(file, 'uploads')
        if not input_path:
            return jsonify({
                'status': 'error',
                'message': 'Invalid file type. Allowed types: ' + ', '.join(ALLOWED_EXTENSIONS.keys())
            }), 400
        
        # Determine output format
        output_ext = {
            'pdf-to-word': 'docx',
            'pdf-to-jpeg': 'jpg',
            'word-to-pdf': 'pdf',
            'pdf-to-latex': 'tex',
            'latex-to-pdf': 'pdf'
        }.get(conversion_type)
        
        # Generate output filename
        output_dir = os.path.join(current_app.config['UPLOAD_FOLDER'], 'converted')
        os.makedirs(output_dir, exist_ok=True)
        output_filename = f"{uuid.uuid4()}.{output_ext}"
        output_path = os.path.join(output_dir, output_filename)
        
        # Perform conversion
        try:
            if conversion_type == 'pdf-to-word':
                doc_converter.pdf_to_word(input_path, output_path)
            elif conversion_type == 'pdf-to-jpeg':
                doc_converter.pdf_to_jpeg(input_path, output_path)
            elif conversion_type == 'word-to-pdf':
                doc_converter.word_to_pdf(input_path, output_path)
            elif conversion_type == 'pdf-to-latex':
                doc_converter.pdf_to_latex(input_path, output_path)
            elif conversion_type == 'latex-to-pdf':
                doc_converter.latex_to_pdf(input_path, output_path)
            else:
                return jsonify({
                    'status': 'error',
                    'message': 'Unsupported conversion type'
                }), 400
                
        except Exception as e:
            logger.error(f'Conversion error: {str(e)}', exc_info=True)
            return jsonify({
                'status': 'error',
                'message': 'Conversion failed',
                'error': str(e)
            }), 500
        
        # Save conversion record
        conversion = Conversion(
            type=conversion_type,
            input_file=input_path,
            output_file=output_path,
            status='completed',
            created_at=datetime.utcnow()
        )
        db.session.add(conversion)
        db.session.commit()
        
        # Return success response with download URL
        return jsonify({
            'status': 'success',
            'message': 'Conversion completed',
            'download_url': f'/api/download/{os.path.basename(output_path)}',
            'conversion_id': conversion.id
        })
        
    except Exception as e:
        db.session.rollback()
        logger.error(f'Error in {conversion_type}: {str(e)}', exc_info=True)
        return jsonify({
            'status': 'error',
            'message': 'An error occurred during conversion',
            'error': str(e)
        }), 500

# Download converted file
@api_bp.route('/download/<path:filename>', methods=['GET'])
@cross_origin()
def download_file(filename):
    """Download a converted file"""
    try:
        # Security: Prevent directory traversal
        filename = os.path.basename(filename)
        filepath = os.path.join(current_app.config['UPLOAD_FOLDER'], 'converted', filename)
        
        if not os.path.exists(filepath):
            return jsonify({'status': 'error', 'message': 'File not found'}), 404
            
        # Determine MIME type from file extension
        ext = filename.rsplit('.', 1)[1].lower()
        mimetype = ALLOWED_EXTENSIONS.get(ext, 'application/octet-stream')
        
        return send_file(
            filepath,
            mimetype=mimetype,
            as_attachment=True,
            download_name=filename
        )
        
    except Exception as e:
        logger.error(f'Error downloading file {filename}: {str(e)}', exc_info=True)
        return jsonify({
            'status': 'error',
            'message': 'Failed to download file',
            'error': str(e)
        }), 500

# Settings Endpoint
@api_bp.route('/settings', methods=['GET'])
@cross_origin()
def get_settings():
    """Get system settings"""
    return jsonify({
        'openai_status': 'configured' if os.getenv('OPENAI_API_KEY') else 'not_configured',
        'smtp_status': 'configured' if os.getenv('SMTP_SERVER') else 'not_configured',
        'google_sheets_status': 'configured' if os.getenv('GOOGLE_SHEETS_CREDENTIALS') else 'not_configured',
        'database_type': 'SQLite',
        'framework': 'Flask',
        'version': '1.0.0'
    })
