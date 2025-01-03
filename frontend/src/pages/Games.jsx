import { Link } from "react-router-dom";
import '../styles/Games.css';

function Games() {
    return (
        <div className="games">
            <h1>Guess the NBA Player</h1>
            <div className="game-link">
                <Link to="/games/classic" className="button">Classic</Link>
                <p className="link-description">Guess the player from their silhouette (current players).</p>
            </div>
            <div className="game-link">
                <Link to="/games/team" className="button">Past Team Logo</Link>
                <p className="link-description">Guess the player based on their past teams' logos.</p>
            </div>
            <div className="game-link">
                <Link to="/games/bio" className="button">Biography</Link>
                <p className="link-description">Guess the player based on their bio.</p>
            </div>
            <div className="game-link">
                <Link to="/games/hard" className="button">Hard Mode</Link>
                <p className="link-description">Guess the player from their silhouette (past players included).</p>
            </div>
        </div>
    );
}

export default Games;
