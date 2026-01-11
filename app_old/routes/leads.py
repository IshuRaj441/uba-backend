from flask import Blueprint, request, jsonify, current_app
from app import db
from app.models import Lead, ScrapeJob, ExportJob
from datetime import datetime, timedelta
import json
import os
from werkzeug.utils import secure_filename
import pandas as pd
from sqlalchemy import func

bp = Blueprint('leads', __name__)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in {'csv', 'xlsx', 'xls'}

@bp.route('/api/leads', methods=['GET'])
def get_leads():
    # Pagination
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    
    # Filtering
    query = Lead.query
    
    if request.args.get('status'):
        query = query.filter(Lead.status == request.args.get('status'))
    
    if request.args.get('source'):
        query = query.filter(Lead.source == request.args.get('source'))
    
    if request.args.get('search'):
        search = f"%{request.args.get('search')}%"
        query = query.filter(
            (Lead.name.ilike(search)) | 
            (Lead.email.ilike(search)) |
            (Lead.company.ilike(search))
        )
    
    # Sorting
    sort_by = request.args.get('sort_by', 'created_at')
    sort_order = request.args.get('sort_order', 'desc')
    
    if hasattr(Lead, sort_by):
        column = getattr(Lead, sort_by)
        if sort_order == 'desc':
            column = column.desc()
        query = query.order_by(column)
    
    # Execute query with pagination
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)
    leads = pagination.items
    
    return jsonify({
        'items': [lead.to_dict() for lead in leads],
        'total': pagination.total,
        'pages': pagination.pages,
        'current_page': page,
        'per_page': per_page
    })

@bp.route('/api/leads/<int:id>', methods=['GET'])
def get_lead(id):
    lead = Lead.query.get_or_404(id)
    return jsonify(lead.to_dict())

@bp.route('/api/leads/<int:id>', methods=['PUT'])
def update_lead(id):
    lead = Lead.query.get_or_404(id)
    data = request.get_json()
    
    for field in ['name', 'email', 'phone', 'company', 'position', 'source', 'status', 'notes']:
        if field in data:
            setattr(lead, field, data[field])
    
    db.session.commit()
    return jsonify(lead.to_dict())

@bp.route('/api/leads/<int:id>', methods=['DELETE'])
def delete_lead(id):
    lead = Lead.query.get_or_404(id)
    db.session.delete(lead)
    db.session.commit()
    return '', 204

@bp.route('/api/scrape', methods=['POST'])
def scrape_leads():
    data = request.get_json()
    url = data.get('url')
    
    if not url:
        return jsonify({'error': 'URL is required'}), 400
    
    # Create a new scrape job
    job = ScrapeJob(url=url, status='pending')
    db.session.add(job)
    db.session.commit()
    
    # In a real application, you would use a task queue like Celery here
    # For now, we'll simulate the scraping process
    try:
        # TODO: Implement actual web scraping logic
        # This is a placeholder that simulates finding leads
        import random
        from faker import Faker
        
        fake = Faker()
        num_leads = random.randint(5, 15)
        
        for _ in range(num_leads):
            lead = Lead(
                name=fake.name(),
                email=fake.email(),
                phone=fake.phone_number(),
                company=fake.company(),
                position=fake.job(),
                source=url,
                status='new'
            )
            db.session.add(lead)
        
        job.status = 'completed'
        job.result_count = num_leads
        job.completed_at = datetime.utcnow()
        db.session.commit()
        
        return jsonify({
            'job_id': job.id,
            'status': 'completed',
            'leads_created': num_leads
        })
        
    except Exception as e:
        db.session.rollback()
        job.status = 'failed'
        job.error = str(e)
        job.completed_at = datetime.utcnow()
        db.session.commit()
        return jsonify({'error': str(e)}), 500

@bp.route('/api/export/csv', methods=['POST'])
def export_csv():
    try:
        query = Lead.query
        leads = query.all()
        
        # Create a DataFrame from the leads
        data = [{
            'Name': lead.name,
            'Email': lead.email,
            'Phone': lead.phone,
            'Company': lead.company,
            'Position': lead.position,
            'Source': lead.source,
            'Status': lead.status,
            'Created At': lead.created_at.isoformat() if lead.created_at else ''
        } for lead in leads]
        
        df = pd.DataFrame(data)
        
        # Create export directory if it doesn't exist
        export_dir = os.path.join(current_app.root_path, '..', 'exports')
        os.makedirs(export_dir, exist_ok=True)
        
        # Generate filename with timestamp
        timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
        filename = f'leads_export_{timestamp}.csv'
        filepath = os.path.join(export_dir, filename)
        
        # Save to CSV
        df.to_csv(filepath, index=False)
        
        # Create export job record
        job = ExportJob(
            export_type='csv',
            status='completed',
            file_path=filepath,
            completed_at=datetime.utcnow()
        )
        db.session.add(job)
        db.session.commit()
        
        return jsonify({
            'status': 'completed',
            'file': filename,
            'count': len(leads)
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@bp.route('/api/export/sheets', methods=['POST'])
def export_sheets():
    try:
        # This is a placeholder for Google Sheets export
        # In a real implementation, you would use the Google Sheets API
        # For now, we'll just return a success message
        
        job = ExportJob(
            export_type='sheets',
            status='completed',
            completed_at=datetime.utcnow()
        )
        db.session.add(job)
        db.session.commit()
        
        return jsonify({
            'status': 'completed',
            'message': 'Export to Google Sheets initiated',
            'job_id': job.id
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@bp.route('/api/export/pdf', methods=['POST'])
def export_pdf():
    try:
        # This is a placeholder for PDF export
        # In a real implementation, you would generate a PDF
        
        job = ExportJob(
            export_type='pdf',
            status='completed',
            completed_at=datetime.utcnow()
        )
        db.session.add(job)
        db.session.commit()
        
        return jsonify({
            'status': 'completed',
            'message': 'PDF export initiated',
            'job_id': job.id
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@bp.route('/api/stats', methods=['GET'])
def get_stats():
    # Total leads
    total_leads = db.session.query(func.count(Lead.id)).scalar()
    
    # Leads added today
    today = datetime.utcnow().date()
    tomorrow = today + timedelta(days=1)
    leads_today = db.session.query(func.count(Lead.id)).filter(
        Lead.created_at >= today,
        Lead.created_at < tomorrow
    ).scalar()
    
    # Leads by source
    sources = db.session.query(
        Lead.source,
        func.count(Lead.id).label('count')
    ).group_by(Lead.source).all()
    
    # Last scrape job
    last_scrape = ScrapeJob.query.order_by(ScrapeJob.completed_at.desc()).first()
    
    return jsonify({
        'total_leads': total_leads,
        'leads_today': leads_today,
        'sources': [{'name': s[0], 'count': s[1]} for s in sources],
        'last_scrape': last_scrape.to_dict() if last_scrape else None
    })
