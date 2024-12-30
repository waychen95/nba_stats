import { useState } from 'react';
import '../styles/Contact.css';

function Contact() {
  const [formData, setFormData] = useState({ email: '', message: '', first_name: '', last_name: '' });
  const [status, setStatus] = useState('');

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData({ ...formData, [name]: value });
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setStatus(''); // Clear status on new submission

    // Basic validation
    if (!formData.email || !formData.message || !formData.first_name || !formData.last_name) {
      setStatus('Please fill out all fields.');
      return;
    }

    try {
      const response = await fetch('http://localhost:5000/api/contact', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(formData),
      });

      if (response.ok) {
        setFormData({ email: '', message: '', first_name: '', last_name: '' }); // Reset form
        setStatus('Your message has been sent!');
      } else {
        const errorData = await response.json();
        setStatus(`Error: ${errorData.message || 'Failed to send message.'}`);
      }
    } catch (error) {
      setStatus('An error occurred. Please try again.');
    }
  };

  return (
    <div className="contact-container">
      <h1>Contact Us</h1>
      <form id="contact-form" onSubmit={handleSubmit}>
        <label className="form-label">
          Email:
          <input
            type="email"
            name="email"
            className="form-input"
            value={formData.email}
            onChange={handleChange}
            required
          />
        </label>
        <label className="form-label">
          First Name:
          <input
            type="text"
            name="first_name"
            className="form-input"
            value={formData.first_name}
            onChange={handleChange}
            required
          />
        </label>
        <label className="form-label">
          Last Name:
          <input
            type="text"
            name="last_name"
            className="form-input"
            value={formData.last_name}
            onChange={handleChange}
            required
          />
        </label>
        <label className="form-label">
          Message:
          <textarea
            name="message"
            className="form-input"
            value={formData.message}
            onChange={handleChange}
            required
          />
        </label>
        <button type="submit" className="contact-button">Submit</button>
      </form>
      {status && <p className={`status-message ${status.includes('error') ? 'error' : ''}`}>{status}</p>}
    </div>
  );
}

export default Contact;
