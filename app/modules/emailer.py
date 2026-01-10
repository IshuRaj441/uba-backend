"""
Email Automation Module

This module provides functionality to send emails with various options.
"""
import smtplib
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication
from email.utils import formatdate, make_msgid
from typing import List, Optional, Union, Dict, Any
import os

logger = logging.getLogger(__name__)

class EmailAutomation:
    """
    A class to handle email automation with support for HTML content and attachments.
    
    This implementation uses Python's built-in smtplib for sending emails.
    """
    
    def __init__(self, 
                 smtp_server: str = 'smtp.gmail.com',
                 smtp_port: int = 587,
                 use_tls: bool = True,
                 username: Optional[str] = None,
                 password: Optional[str] = None):
        """
        Initialize the email automation with SMTP settings.
        
        Args:
            smtp_server: SMTP server address
            smtp_port: SMTP server port
            use_tls: Whether to use TLS encryption
            username: SMTP username (if authentication is required)
            password: SMTP password (if authentication is required)
        """
        self.smtp_server = smtp_server
        self.smtp_port = smtp_port
        self.use_tls = use_tls
        self.username = username
        self.password = password
    
    def send_email(self,
                  to_emails: Union[str, List[str]],
                  subject: str,
                  body: str,
                  from_email: Optional[str] = None,
                  cc_emails: Optional[Union[str, List[str]]] = None,
                  bcc_emails: Optional[Union[str, List[str]]] = None,
                  reply_to: Optional[str] = None,
                  is_html: bool = False,
                  attachments: Optional[List[Dict[str, Any]]] = None) -> bool:
        """
        Send an email with optional attachments.
        
        Args:
            to_emails: Email address or list of email addresses to send to
            subject: Email subject
            body: Email body content
            from_email: Sender's email address (defaults to username if not provided)
            cc_emails: CC email address or list of addresses
            bcc_emails: BCC email address or list of addresses
            reply_to: Reply-to email address
            is_html: Whether the body contains HTML content
            attachments: List of attachment dictionaries with 'file_path' and 'filename' keys
            
        Returns:
            bool: True if email was sent successfully, False otherwise
        """
        try:
            # Prepare email addresses
            from_email = from_email or self.username
            if not from_email:
                raise ValueError("Sender email address is required")
                
            if not to_emails:
                raise ValueError("At least one recipient email address is required")
                
            # Convert single email to list if needed
            if isinstance(to_emails, str):
                to_emails = [to_emails]
            if cc_emails and isinstance(cc_emails, str):
                cc_emails = [cc_emails]
            if bcc_emails and isinstance(bcc_emails, str):
                bcc_emails = [bcc_emails]
            
            # Create message container
            msg = MIMEMultipart()
            msg['From'] = from_email
            msg['To'] = ', '.join(to_emails)
            msg['Subject'] = subject
            msg['Date'] = formatdate(localtime=True)
            
            if cc_emails:
                msg['Cc'] = ', '.join(cc_emails)
            if bcc_emails:
                msg['Bcc'] = ', '.join(bcc_emails)
            if reply_to:
                msg.add_header('Reply-To', reply_to)
            
            # Add message ID for tracking
            msg['Message-ID'] = make_msgid()
            
            # Attach the body
            content_type = 'html' if is_html else 'plain'
            msg.attach(MIMEText(body, content_type, 'utf-8'))
            
            # Add attachments if any
            if attachments:
                for attachment in attachments:
                    file_path = attachment.get('file_path')
                    filename = attachment.get('filename', os.path.basename(file_path))
                    
                    if not file_path or not os.path.exists(file_path):
                        logger.warning(f"Attachment not found: {file_path}")
                        continue
                    
                    with open(file_path, 'rb') as f:
                        part = MIMEApplication(f.read(), Name=filename)
                        part['Content-Disposition'] = f'attachment; filename="{filename}"'
                        msg.attach(part)
            
            # Connect to SMTP server and send email
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                if self.use_tls:
                    server.starttls()
                
                if self.username and self.password:
                    server.login(self.username, self.password)
                
                # Combine all recipients
                all_recipients = to_emails.copy()
                if cc_emails:
                    all_recipients.extend(cc_emails)
                if bcc_emails:
                    all_recipients.extend(bcc_emails)
                
                # Send email
                server.send_message(msg)
                logger.info(f"Email sent successfully to {', '.join(to_emails)}")
                return True
                
        except Exception as e:
            logger.error(f"Failed to send email: {str(e)}", exc_info=True)
            return False

# Example usage
if __name__ == "__main__":
    # Example with Gmail (make sure to enable less secure apps or use app password)
    emailer = EmailAutomation(
        smtp_server='smtp.gmail.com',
        smtp_port=587,
        use_tls=True,
        username='your-email@gmail.com',
        password='your-password-or-app-password'
    )
    
    # Send a simple email
    emailer.send_email(
        to_emails='recipient@example.com',
        subject='Test Email',
        body='This is a test email sent from EmailAutomation.',
        is_html=False
    )
    
    # Send an HTML email with attachment
    emailer.send_email(
        to_emails=['recipient1@example.com', 'recipient2@example.com'],
        subject='HTML Email with Attachment',
        body='<h1>Hello!</h1><p>This is an <b>HTML</b> email with an attachment.</p>',
        is_html=True,
        attachments=[
            {'file_path': 'path/to/your/file.pdf', 'filename': 'document.pdf'}
        ]
    )
