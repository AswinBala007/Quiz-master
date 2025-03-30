import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText


SMTP_SERVER = "localhost"
SMTP_PORT = 1025
SENDER_EMAIL = 'admin@quiz.com'
SENDER_PASSWORD = ''

def send_email(to, subject, content):

    msg = MIMEMultipart()
    msg['To'] = to
    msg['Subject'] = subject
    msg['From'] = SENDER_EMAIL

    msg.attach(MIMEText(content,'html'))

    with smtplib.SMTP(host=SMTP_SERVER, port=SMTP_PORT) as client:
        client.send_message(msg)
        client.quit()

def send_reminder_mail(user_email, user_name):
    """Send email via SMTP"""
    try:
        # Create the email message
        msg = MIMEMultipart()
        msg["From"] = "admin@quiz.com"
        msg["To"] = user_email
        msg["Subject"] = "Reminder: New Quizzes Available"
        
        # Compose the body of the email
        message_body = f"Hello {user_name},\n\nNew quizzes are available! Log in and take a look."
        msg.attach(MIMEText(message_body, "plain"))
        
        # Send email via SMTP
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()  # Secure the connection
            # server.login(SMTP_USERNAME, SMTP_PASSWORD)  # Authenticate
            # server.sendmail(EMAIL_FROM, user_email, msg.as_string())  # Send email
        
        print(f"Email sent to {user_email}")

    except Exception as e:
        print(f"Error sending email to {user_email}: {str(e)}")
# send_email('aditya@example.com', 'Test Email', '<h1> Welcome to AppDev </h1>')