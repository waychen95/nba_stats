import '../styles/Home.css';
import { Link } from 'react-router-dom';

function Home() {
  return (
    <div id="container">
      <img src="/nba_logo.png" alt="NBA Logo" />
      <div id='button-container'>
        <Link to="/games" className='button'>Guess The Player</Link>
        <Link to="/chatbot" className='button'>NBAdle AI</Link>
        <Link to="/teams" className='button'>Teams</Link>
        <Link to="/players" className='button'>Players</Link>
      </div>
      <div className='call_to_action'>
        <h2>Interested in joining?</h2>
        <Link to="/contact" className='button contact'>Contact Us</Link>
        {/* <h3>Already have an account? <a href='/login' id='acount-a-tag'>Log In</a></h3> */}
      </div>
    </div>
  );
}

export default Home;