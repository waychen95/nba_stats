import '../styles/Home.css';
import { Link } from 'react-router-dom';

function Home() {
  return (
    <div id="container">
      <img src="../public/nba_logo.png" alt="NBA Logo" />
      <div id='button-container'>
        <Link to="/guess-the-player" className='button'>Guess The Player</Link>
        <Link to="/teams" className='button'>Teams</Link>
        <Link to="/players" className='button'>Players</Link>
      </div>
      <div className='call_to_action'>
        <h2>Want to lock in your favorite team/player?</h2>
        <Link to="/signup" className='button signup'>Sign Up</Link>
        <h3>Already have an account? <a href='#' id='acount-a-tag'>Log In</a></h3>
      </div>
    </div>
  );
}

export default Home;