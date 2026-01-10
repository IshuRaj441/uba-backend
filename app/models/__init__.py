"""
Database models for the Universal Business Automation system.
"""
from .user import User
from .lead import Lead, ScrapeJob, ExportJob
from .document import Document, ConversionJob
from .email import Email, EmailTemplate, EmailLog
from .activity import ActivityLog

# Import all models here to ensure they are registered with SQLAlchemy
__all__ = [
    'User',
    'Lead', 
    'ScrapeJob', 
    'ExportJob',
    'Document',
    'ConversionJob',
    'Email',
    'EmailTemplate',
    'EmailLog',
    'ActivityLog'
]
