import { Link } from "react-router-dom";
import '../styles/Games.css';

function Games() {
    return (
        <div className="games">
            <h1>Guess the NBA Player</h1>
            <Link to="/games/image" className="button">Classic</Link>
            <Link to="/games/team" className="button">Team Logo</Link>
        </div>
    );
}

export default Games;