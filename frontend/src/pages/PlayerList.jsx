import { useState, useEffect } from 'react';
import { BrowserRouter as Router, Route, Routes, Link } from 'react-router-dom';
import Player from './Player';
import '../styles/PlayerList.css';

function PlayerList() {
  const [players, setPlayers] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function fetchPlayers() {
      const response = await fetch('http://localhost:5000/players');
      const data = await response.json();
      setPlayers(data.players);
      setLoading(false);
    }

    fetchPlayers();
  }, []);

  return (
      <div className='player-list-container'>
        <h1>Players</h1>
        {loading ? (
          <p>Loading...</p>
        ) : (
          <ul className='player-list'>
            {players.map((player) => (
              <Link to={`/players/${player.id}`} key={player.id} className='player-card'>
                <img src={player.image_url}></img>
                <p>{player.first_name} {player.last_name}</p>
              </Link>
            ))}
          </ul>
        )}
      </div>

  );
}

export default PlayerList;