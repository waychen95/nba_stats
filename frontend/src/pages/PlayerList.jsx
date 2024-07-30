import { useState, useEffect } from 'react';
import { BrowserRouter as Router, Route, Routes, Link } from 'react-router-dom';
import Player from './Player';

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
      <div>
      <h1>Players</h1>
      {loading ? (
        <p>Loading...</p>
      ) : (
        <ul>
          {players.map((player) => (
            <li key={player.id}>
              <Link to={`/players/${player.id}`}>{player.first_name} {player.last_name} {player.id}</Link>
            </li>
          ))}
        </ul>
      )}
      </div>

  );
}

export default PlayerList;