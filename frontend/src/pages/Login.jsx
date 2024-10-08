import '../styles/Login.css';

function Login() {
  return (
    <div className="login-container">
      <h1>Login</h1>
      <form id="login-form">
        <label class="form-label">
            Email:
            <input type="text" name="email" class="form-input" />
        </label>
        <label class="form-label">
            Password:
            <input type="password" name="password" class="form-input" />
        </label>
        <button type="submit" class="login-button">Login</button>
        </form>
    </div>
  );
}

export default Login;