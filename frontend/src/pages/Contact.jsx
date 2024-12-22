import '../styles/Contact.css';

function Contact() {
  return (
    <div className="contact-container">
      <h1>Contact Form</h1>
      <form id="contact-form">
        <label class="form-label">
            Email:
            <input type="text" name="email" class="form-input" />
        </label>
        <label class="form-label">
            Message:
            <textarea name="message" class="form-input" />
        </label>
        <button type="submit" class="button">Submit</button>
        </form>
    </div>
  );
}

export default Contact;