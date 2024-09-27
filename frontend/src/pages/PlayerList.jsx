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
  const [currentPage, setCurrentPage] = useState(1);
  const [playersPerPage] = useState(24); // Number of players per page
  const [totalPages, setTotalPages] = useState(1); // Total number of pages

  const team_list = [
    "HOU", "MIA", "TOR", "DAL", "MEM", "DEN", "MIN", "PHX", "NYK", "POR", "WAS", "CHA",
    "CHI", "LAC", "SAS", "CLE", "NOP", "GSW", "MIL", "ORL", "IND", "SAC", "OKC", "LAL",
    "UTA", "DET", "ATL", "BKN", "PHI", "BOS"
  ];

  useEffect(() => {
    async function fetchPlayers() {
      setLoading(true);
      let url = `http://localhost:5000/players?order=${order}&page=${currentPage}&limit=${playersPerPage}`;
      if (team) {
        url += `&team=${team}`;
      }
      if (search) {
        url += `&search=${search}`;
      }
      const response = await fetch(url);
      const data = await response.json();
      setPlayers(data.players);
      setTotalPages(Math.ceil(data.total / playersPerPage)); // Assuming API returns `total` count
      setLoading(false);
    }

    fetchPlayers();
  }, [order, team, search, currentPage]); // Fetch players when page, order, team, or search changes

  const handlePageChange = (pageNumber) => {
    setCurrentPage(pageNumber);
  };

  const renderPagination = () => {
    const pageNumbers = [];
    const startPage = Math.max(1, currentPage - 5); // Start 5 pages before the current page
    const endPage = Math.min(totalPages, currentPage + 5); // End 5 pages after the current page
  
    for (let i = startPage; i <= endPage; i++) {
      pageNumbers.push(i);
    }
  
    return (
      <div className='pagination'>
        {currentPage > 1 && (
          <button
            className='page-button'
            onClick={() => handlePageChange(currentPage - 1)}
          >
            Previous
          </button>
        )}
        
        {pageNumbers.map(number => (
          <button
            key={number}
            className={`page-button ${currentPage === number ? 'active' : ''}`}
            onClick={() => handlePageChange(number)}
          >
            {number}
          </button>
        ))}
  
        {currentPage < totalPages && (
          <button
            className='page-button'
            onClick={() => handlePageChange(currentPage + 1)}
          >
            Next
          </button>
        )}
      </div>
    );
  };
  

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
        <>
          <ul className='player-list'>
            {players.map((player) => (
              <Link to={`/players/${player.id}`} key={player.id} className='player-card'>
                <img src={player.image_url} alt={`${player.first_name} ${player.last_name}`} />
                <p>{player.first_name} {player.last_name}</p>
              </Link>
            ))}
          </ul>
          {renderPagination()}
        </>
      )}
    </div>
  );
}

export default PlayerList;