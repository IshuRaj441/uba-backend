from flask import Blueprint, request, jsonify, send_file
from werkzeug.utils import secure_filename
import os
import subprocess
from datetime import datetime
from .. import db
from ..models import Lead, Document, ConversionJob

api = Blueprint('api', __name__)

# Helper function to handle file uploads
def save_uploaded_file(file, subfolder=''):
    if not file:
        return None
    
    # Create uploads directory if it doesn't exist
    upload_dir = os.path.join(current_app.config['UPLOAD_FOLDER'], subfolder)
    os.makedirs(upload_dir, exist_ok=True)
    
    # Save file
    filename = secure_filename(file.filename)
    filepath = os.path.join(upload_dir, filename)
    file.save(filepath)
    return filepath

# Lead Engine
@api.route('/api/scrape', methods=['POST'])
def scrape_leads():
    data = request.get_json()
    url = data.get('url')
    # TODO: Implement actual scraping logic
    return jsonify({"status": "success", "message": "Scraping initiated"})

@api.route('/api/leads', methods=['GET'])
def get_leads():
    leads = Lead.query.all()
    return jsonify([{
        'id': lead.id,
        'name': lead.name,
        'email': lead.email,
        'source': lead.source,
        'created_at': lead.created_at.isoformat()
    } for lead in leads])

# Document Generator
@api.route('/api/pdf/create', methods=['POST'])
def create_pdf():
    data = request.get_json()
    # TODO: Implement PDF generation
    return jsonify({"status": "success", "message": "PDF generated"})

@api.route('/api/pdfs', methods=['GET'])
def list_pdfs():
    pdfs = Document.query.filter_by(document_type='pdf').all()
    return jsonify([{
        'id': doc.id,
        'name': doc.name,
        'created_at': doc.created_at.isoformat()
    } for doc in pdfs])

# File Conversion Engine
@api.route('/api/convert/pdf-to-word', methods=['POST'])
def convert_pdf_to_word():
    if 'file' not in request.files:
        return jsonify({"error": "No file provided"}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "No selected file"}), 400
        
    # Save the uploaded file
    filepath = save_uploaded_file(file, 'conversions')
    
    try:
        # TODO: Implement actual conversion using appropriate library
        # This is a placeholder for the conversion logic
        output_path = filepath + '.docx'
        
        # Create conversion record
        conversion = ConversionJob(
            source_file=filepath,
            target_file=output_path,
            conversion_type='pdf-to-word',
            status='completed'
        )
        db.session.add(conversion)
        db.session.commit()
        
        return send_file(output_path, as_attachment=True)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Similar endpoints for other conversion types
@api.route('/api/convert/word-to-pdf', methods=['POST'])
def convert_word_to_pdf():
    # Similar implementation as above
    pass

@api.route('/api/convert/pdf-to-jpeg', methods=['POST'])
def convert_pdf_to_jpeg():
    # Similar implementation as above
    pass

@api.route('/api/convert/pdf-to-latex', methods=['POST'])
def convert_pdf_to_latex():
    # Similar implementation as above
    pass

@api.route('/api/convert/latex-to-pdf', methods=['POST'])
def compile_latex_to_pdf():
    if 'file' not in request.files:
        return jsonify({"error": "No file provided"}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "No selected file"}), 400
    
    # Save the uploaded file
    filepath = save_uploaded_file(file, 'latex')
    
    try:
        # Compile LaTeX to PDF
        output_dir = os.path.dirname(filepath)
        result = subprocess.run(
            ['pdflatex', '-output-directory', output_dir, filepath],
            capture_output=True,
            text=True
        )
        
        if result.returncode != 0:
            return jsonify({
                "error": "LaTeX compilation failed",
                "details": result.stderr
            }), 500
            
        # The output PDF will have the same name but with .pdf extension
        output_pdf = os.path.splitext(filepath)[0] + '.pdf'
        
        # Create conversion record
        conversion = ConversionJob(
            source_file=filepath,
            target_file=output_pdf,
            conversion_type='latex-to-pdf',
            status='completed'
        )
        db.session.add(conversion)
        db.session.commit()
        
        return send_file(output_pdf, as_attachment=True)
    except Exception as e:
        return jsonify({"error": str(e)}), 500
