from flask import Flask, request, jsonify
from flask_cors import CORS
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

app = Flask(__name__)
CORS(app)

# Email configuration
SMTP_SERVER = 'smtp.gmail.com'  # For Gmail; replace if using a different provider
SMTP_PORT = 587
EMAIL_ADDRESS = 'your-email@gmail.com'  # Your email
EMAIL_PASSWORD = 'your-email-password'  # Your email password (consider using app passwords for security)

@app.route('/api/contact', methods=['POST'])
def contact():
    data = request.json
    email = data.get('email')
    message = data.get('message')

    if not email or not message:
        return jsonify({'error': 'Missing fields'}), 400

    try:
        # Set up the email
        msg = MIMEMultipart()
        msg['From'] = EMAIL_ADDRESS
        msg['To'] = EMAIL_ADDRESS  # You receive the email
        msg['Subject'] = f"Contact Form Submission from {email}"
        msg.attach(MIMEText(message, 'plain'))

        # Send the email
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()
            server.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
            server.send_message(msg)

        return jsonify({'success': 'Message sent successfully'}), 200
    except Exception as e:
        print(f"Error sending email: {e}")
        return jsonify({'error': 'Error sending message'}), 500

if __name__ == '__main__':
    app.run(port=5000)
