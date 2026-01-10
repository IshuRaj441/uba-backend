"""
Application routes for the Universal Business Automation Dashboard
"""
from flask import Blueprint, jsonify, request, current_app
from . import db
from .models import User, Lead, EmailLog, PDFReport, SocialPost, ScheduledTask, ActivityLog, Conversion
from werkzeug.utils import secure_filename
import os
from datetime import datetime, timezone

# Create blueprints
api_bp = Blueprint('api', __name__)
main_bp = Blueprint('main', __name__)

# API Routes
@api_bp.route('/health', methods=['GET'])
@api_bp.route('/health/', methods=['GET'])
def health_check():
    """Health check endpoint"""
    try:
        # Test database connection
        db.session.execute('SELECT 1')
        db_status = 'connected'
    except Exception as e:
        db_status = f'error: {str(e)}'
    
    return jsonify({
        'name': 'Universal Business Automation API',
        'status': 'ok',
        'database': db_status,
        'version': '1.0.0',
        'timestamp': datetime.now(timezone.utc).isoformat()
    })

@api_bp.route('/status')
def status():
    """System status endpoint"""
    try:
        stats = {
            'leads': {
                'total': Lead.query.count(),
                'new': Lead.query.filter_by(status='new').count(),
                'contacted': Lead.query.filter_by(status='contacted').count()
            },
            'emails': {
                'total': EmailLog.query.count(),
                'sent': EmailLog.query.filter_by(status='sent').count(),
                'failed': EmailLog.query.filter(EmailLog.status != 'sent').count()
            },
            'documents': {
                'total': PDFReport.query.count(),
                'templates': PDFReport.query.filter_by(is_template=True).count()
            },
            'system': {
                'users': User.query.count(),
                'active_tasks': ScheduledTask.query.filter_by(is_active=True).count()
            }
        }
        return jsonify(stats)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@api_bp.route('/')
def api_root():
    """API root endpoint"""
    return jsonify({
        'name': 'Universal Business Automation API',
        'version': '1.0.0',
        'endpoints': {
            'health': '/api/health',
            'status': '/api/status',
            'leads': '/api/leads',
            'emails': '/api/emails',
            'documents': '/api/documents',
            'conversions': '/api/conversions'
        }
    })

# Main Routes
@main_bp.route('/')
def index():
    """Main dashboard page"""
    return jsonify({
        'name': 'Universal Business Automation Dashboard',
        'status': 'running',
        'version': '1.0.0',
        'message': 'Welcome to the Universal Business Automation API',
        'timestamp': datetime.now(timezone.utc).isoformat(),
        'endpoints': {
            'health': '/api/health',
            'status': '/api/status',
            'leads': '/api/leads',
            'documents': '/api/documents',
            'emails': '/api/emails',
            'conversions': '/api/conversions',
            'pdfs': '/api/pdfs'
        }
    })

@main_bp.route('/test')
def test():
    """Test endpoint to verify the server is running"""
    return jsonify({
        'status': 'success',
        'message': 'Server is running!',
        'timestamp': datetime.now(timezone.utc).isoformat()
    })

# Add more routes as needed
@main_bp.route('/api/leads', methods=['GET'])
def get_leads():
    """Get all leads with pagination"""
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    
    query = Lead.query
    
    # Apply filters
    if 'status' in request.args:
        query = query.filter_by(status=request.args['status'])
    
    if 'search' in request.args:
        search = f"%{request.args['search']}%"
        query = query.filter(Lead.name.ilike(search) | 
                           Lead.email.ilike(search) |
                           Lead.phone.ilike(search))
    
    # Apply sorting
    sort_by = request.args.get('sort_by', 'created_at')
    sort_order = request.args.get('sort_order', 'desc')
    
    if hasattr(Lead, sort_by):
        column = getattr(Lead, sort_by)
        if sort_order.lower() == 'desc':
            column = column.desc()
        query = query.order_by(column)
    
    # Paginate results
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)
    leads = [lead.to_dict() for lead in pagination.items]
    
    return jsonify({
        'items': leads,
        'total': pagination.total,
        'pages': pagination.pages,
        'current_page': page,
        'per_page': per_page
    })

# Error handlers
@api_bp.errorhandler(404)
def not_found_error(error):
    return jsonify({'error': 'Not found'}), 404

@api_bp.errorhandler(500)
def internal_error(error):
    db.session.rollback()
    return jsonify({'error': 'Internal server error'}), 500
