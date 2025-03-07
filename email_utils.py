import os
from flask_mail import Mail, Message
from flask import current_app

mail = Mail()

def init_mail(app):
    # Use environment variables loaded by python-dotenv
    app.config.update(
        MAIL_SERVER=os.getenv("MAIL_SERVER"),
        MAIL_PORT=int(os.getenv("MAIL_PORT", 587)),
        MAIL_USE_TLS=os.getenv("MAIL_USE_TLS") == "True",
        MAIL_USERNAME=os.getenv("MAIL_USERNAME"),
        MAIL_PASSWORD=os.getenv("MAIL_PASSWORD"),
        MAIL_DEFAULT_SENDER=os.getenv("MAIL_DEFAULT_SENDER")
    )
    mail.init_app(app)

def send_notification(to, subject, body):
    msg = Message(subject=subject, recipients=[to], body=body)
    mail.send(msg)
