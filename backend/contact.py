from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_mail import Mail, Message

app = Flask(__name__)
CORS(app)

# Flask-Mail configuration
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = 'your-email@gmail.com'  # Replace with your Gmail
app.config['MAIL_PASSWORD'] = 'your-email-password'  # Replace with your app password
app.config['MAIL_DEFAULT_SENDER'] = 'your-email@gmail.com'

mail = Mail(app)

@app.route('/api/contact', methods=['POST'])
def contact():
    data = request.get_json()

    # Validate data
    if not data.get('email') or not data.get('message') or not data.get('first_name') or not data.get('last_name'):
        return jsonify({'error': 'All fields are required.'}), 400

    try:
        # Compose email
        msg = Message(
            subject=f"New Contact Form Submission from {data['first_name']} {data['last_name']}",
            recipients=['your-email@gmail.com'],  # Replace with your Gmail
            body=f"Message from {data['first_name']} {data['last_name']} ({data['email']}):\n\n{data['message']}"
        )

        # Send email
        mail.send(msg)
        return jsonify({'message': 'Message sent successfully!'}), 200

    except Exception as e:
        print(e)
        return jsonify({'error': 'Failed to send message.'}), 500


if __name__ == '__main__':
    app.run(debug=True)
