import asyncio
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from app.core.config import settings

class EmailService:
    def __init__(self):
        self.smtp_host = settings.SMTP_HOST
        self.smtp_port = settings.SMTP_PORT
        self.smtp_user = settings.SMTP_USER
        self.smtp_password = settings.SMTP_PASSWORD
        self.email_from = settings.EMAIL_FROM
    
    async def send_verification_code(self, to_email: str, code: str):
        subject = "Подтверждение регистрации в Smart Tracker"
        
        html_content = f"""
        <html>
            <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
                <h2 style="color: #333;">Подтверждение регистрации</h2>
                <p>Здравствуйте!</p>
                <p>Для завершения регистрации введите код подтверждения:</p>
                <div style="background-color: #f4f4f4; padding: 20px; text-align: center; font-size: 32px; letter-spacing: 5px; font-weight: bold;">
                    {code}
                </div>
                <p>Код действителен в течение {settings.VERIFICATION_CODE_EXPIRE_MINUTES} минут.</p>
                <hr>
                <p style="color: #666; font-size: 12px;">С уважением, команда Smart Tracker</p>
            </body>
        </html>
        """
        
        await asyncio.get_event_loop().run_in_executor(
            None, self._send_email_sync, to_email, subject, html_content
        )
    
    def _send_email_sync(self, to_email: str, subject: str, html_content: str):
        msg = MIMEMultipart('alternative')
        msg['Subject'] = subject
        msg['From'] = self.email_from
        msg['To'] = to_email
        
        html_part = MIMEText(html_content, 'html')
        msg.attach(html_part)
        
        with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
            server.starttls()
            server.login(self.smtp_user, self.smtp_password)
            server.send_message(msg)

email_service = EmailService()