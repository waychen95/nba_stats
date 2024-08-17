import { useState, useEffect } from 'react';
import { BrowserRouter as Router, Route, Routes, Link } from 'react-router-dom';
import Player from './Player';
import '../styles/PlayerList.css';

function PlayerList() {
  const [players, setPlayers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [order, setOrder] = useState('asc');
  const [team, setTeam] = useState('');
  const [search, setSearch] = useState('');

  const team_list = [
    "HOU",
    "MIA",
    "TOR",
    "DAL",
    "MEM",
    "DEN",
    "MIN",
    "PHX",
    "NYK",
    "POR",
    "WAS",
    "CHA",
    "CHI",
    "LAC",
    "SAS",
    "CLE",
    "NOP",
    "GSW",
    "MIL",
    "ORL",
    "IND",
    "SAC",
    "OKC",
    "LAL",
    "UTA",
    "DET",
    "ATL",
    "BKN",
    "PHI",
    "BOS"
  ];

  useEffect(() => {
    async function fetchPlayers() {
      let url = `http://localhost:5000/players?order=${order}`;
      if (team) {
        url += `&team=${team}`;
      }
      if (search) {
        url += `&search=${search}`;
      }
      const response = await fetch(url);
      const data = await response.json();
      setPlayers(data.players);
      setLoading(false);
    }

    fetchPlayers();
  }, [order, team, search]); // Trigger fetch when either 'order' or 'team' changes

  return (
    <div className='player-list-container'>
      <h1>Players</h1>
      <div className='player-list-dropdowns'>
        <div className='search-bar'>
              <label>Search Players:</label>
              <input
                type='text'
                placeholder='Search by name...'
                value={search}
                onChange={(e) => setSearch(e.target.value)}
              />
        </div>
        <div className='dropdown-name'>
          <label>Order by name:</label>
          <select value={order} onChange={(e) => setOrder(e.target.value)}>
            <option value='asc'>Ascending</option>
            <option value='desc'>Descending</option>
          </select>
        </div>
        <div className='dropdown-team'>
          <label>Filter by team:</label>
          <select value={team} onChange={(e) => setTeam(e.target.value)}>
            <option value=''>All Teams</option>
            {team_list.sort().map((team) => (
              <option key={team} value={team}>
                {team}
              </option>
            ))}
          </select>
        </div>
      </div>
      {loading ? (
        <div className='player-list'>
          <p className='loading'>Loading...</p>
        </div>
      ) : (
        <ul className='player-list'>
          {players.map((player) => (
            <Link to={`/players/${player.id}`} key={player.id} className='player-card'>
              <img src={player.image_url} alt={`${player.first_name} ${player.last_name}`} />
              <p>{player.first_name} {player.last_name}</p>
            </Link>
          ))}
        </ul>
      )}
    </div>
  );
}

export default PlayerList;
