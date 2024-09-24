import '../styles/Signup.css';

function Signup() {
  return (
    <div className="signup-container">
      <h1>Sign Up</h1>
      <form id="signup-form">
        <label class="form-label">
            Email:
            <input type="text" name="email" class="form-input" />
        </label>
        <label class="form-label">
            Password:
            <input type="password" name="password" class="form-input" />
        </label>
        <button type="submit" class="signup-button">Sign Up</button>
        </form>
    </div>
  );
}

export default Signup;