"""
Email service for sending confirmation emails and notifications.
"""

import smtplib
import ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timedelta
from typing import Optional
import logging
import secrets
import string

from src.core.config import config

logger = logging.getLogger(__name__)

class EmailService:
    """Email service for sending confirmation emails and notifications."""
    
    def __init__(self):
        self.smtp_server = config.smtp_server
        self.smtp_port = config.smtp_port
        self.smtp_username = config.smtp_username
        self.smtp_password = config.smtp_password
        self.smtp_use_tls = config.smtp_use_tls
        self.email_from = config.email_from
        self.app_url = config.app_url
    
    def generate_confirmation_token(self, length: int = 32) -> str:
        """Generate a secure confirmation token."""
        alphabet = string.ascii_letters + string.digits
        return ''.join(secrets.choice(alphabet) for _ in range(length))
    
    def send_email(self, to_email: str, subject: str, html_content: str, text_content: str = None) -> bool:
        """Send an email using SMTP."""
        try:
            # Create message
            message = MIMEMultipart("alternative")
            message["Subject"] = subject
            message["From"] = self.email_from
            message["To"] = to_email
            
            # Add text and HTML parts
            if text_content:
                text_part = MIMEText(text_content, "plain")
                message.attach(text_part)
            
            html_part = MIMEText(html_content, "html")
            message.attach(html_part)
            
            # Send email
            if self.smtp_use_tls:
                context = ssl.create_default_context()
                with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                    server.starttls(context=context)
                    if self.smtp_username and self.smtp_password:
                        server.login(self.smtp_username, self.smtp_password)
                    server.send_message(message)
            else:
                with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                    if self.smtp_username and self.smtp_password:
                        server.login(self.smtp_username, self.smtp_password)
                    server.send_message(message)
            
            logger.info(f"Email sent successfully to {to_email}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send email to {to_email}: {e}")
            return False
    
    def send_confirmation_email(self, to_email: str, username: str, confirmation_token: str) -> bool:
        """Send email confirmation email."""
        subject = "Confirm Your Email - Stock Market Crawler"
        
        confirmation_url = f"{self.app_url}/confirm-email?token={confirmation_token}"
        
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <title>Confirm Your Email</title>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background-color: #4F46E5; color: white; padding: 20px; text-align: center; }}
                .content {{ padding: 20px; background-color: #f9f9f9; }}
                .button {{ display: inline-block; padding: 12px 24px; background-color: #4F46E5; color: white; text-decoration: none; border-radius: 5px; margin: 20px 0; }}
                .footer {{ text-align: center; padding: 20px; color: #666; font-size: 12px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>Welcome to Stock Market Crawler!</h1>
                </div>
                <div class="content">
                    <h2>Hi {username},</h2>
                    <p>Thank you for registering with Stock Market Crawler. To complete your registration and activate your account, please confirm your email address by clicking the button below:</p>
                    
                    <div style="text-align: center;">
                        <a href="{confirmation_url}" class="button">Confirm Email Address</a>
                    </div>
                    
                    <p>If the button doesn't work, you can copy and paste this link into your browser:</p>
                    <p style="word-break: break-all; color: #4F46E5;">{confirmation_url}</p>
                    
                    <p>This confirmation link will expire in 24 hours for security reasons.</p>
                    
                    <p>If you didn't create an account with us, please ignore this email.</p>
                </div>
                <div class="footer">
                    <p>This is an automated message from Stock Market Crawler. Please do not reply to this email.</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        text_content = f"""
        Welcome to Stock Market Crawler!
        
        Hi {username},
        
        Thank you for registering with Stock Market Crawler. To complete your registration and activate your account, please confirm your email address by visiting this link:
        
        {confirmation_url}
        
        This confirmation link will expire in 24 hours for security reasons.
        
        If you didn't create an account with us, please ignore this email.
        
        Best regards,
        Stock Market Crawler Team
        """
        
        return self.send_email(to_email, subject, html_content, text_content)
    
    def send_welcome_email(self, to_email: str, username: str) -> bool:
        """Send welcome email after successful confirmation."""
        subject = "Welcome to Stock Market Crawler - Account Activated!"
        
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <title>Welcome to Stock Market Crawler</title>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background-color: #10B981; color: white; padding: 20px; text-align: center; }}
                .content {{ padding: 20px; background-color: #f9f9f9; }}
                .button {{ display: inline-block; padding: 12px 24px; background-color: #10B981; color: white; text-decoration: none; border-radius: 5px; margin: 20px 0; }}
                .footer {{ text-align: center; padding: 20px; color: #666; font-size: 12px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>🎉 Welcome to Stock Market Crawler!</h1>
                </div>
                <div class="content">
                    <h2>Hi {username},</h2>
                    <p>Great news! Your email has been confirmed and your account is now active. You can now access all features of Stock Market Crawler.</p>
                    
                    <div style="text-align: center;">
                        <a href="{self.app_url}/login" class="button">Login to Your Account</a>
                    </div>
                    
                    <h3>What you can do now:</h3>
                    <ul>
                        <li>📊 Analyze stock market data</li>
                        <li>🔍 Search through financial documents</li>
                        <li>💬 Chat with AI about market insights</li>
                        <li>📈 Get real-time market information</li>
                    </ul>
                    
                    <p>If you have any questions or need assistance, feel free to reach out to our support team.</p>
                    
                    <p>Happy trading!</p>
                </div>
                <div class="footer">
                    <p>Stock Market Crawler Team</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        text_content = f"""
        Welcome to Stock Market Crawler!
        
        Hi {username},
        
        Great news! Your email has been confirmed and your account is now active. You can now access all features of Stock Market Crawler.
        
        Login to your account: {self.app_url}/login
        
        What you can do now:
        - Analyze stock market data
        - Search through financial documents
        - Chat with AI about market insights
        - Get real-time market information
        
        If you have any questions or need assistance, feel free to reach out to our support team.
        
        Happy trading!
        
        Stock Market Crawler Team
        """
        
        return self.send_email(to_email, subject, html_content, text_content)

# Global email service instance
email_service = EmailService() 