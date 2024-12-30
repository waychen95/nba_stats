import React, { useState, useEffect } from 'react';
import { Link, useParams } from 'react-router-dom';
import '../styles/Team.css';

function Team() {
  const { teamId } = useParams();

  const [team, setTeam] = useState({});
  const [loading, setLoading] = useState(true);
  const [players, setPlayers] = useState([]);
  const [teamColor, setTeamColor] = useState('');
  const [playerOption, setPlayerOption] = useState('Current Players');

  const teamColorSchemas = [
    { team: "hawks", colors: "linear-gradient(to bottom, #E03A3E, #C1D32F)" },
    { team: "celtics", colors: "linear-gradient(to bottom, #007A33, #BA9653)" },
    { team: "nets", colors: "linear-gradient(to bottom, #000000, #BEC2C2)" },
    { team: "hornets", colors: "linear-gradient(to bottom, #1D1160, #00788C)" },
    { team: "bulls", colors: "linear-gradient(to bottom, #CE1141, #000000)" },
    { team: "cavaliers", colors: "linear-gradient(to bottom, #860038, #FDBB30)" },
    { team: "mavericks", colors: "linear-gradient(to bottom, #00538C, #B8C4CA)" },
    { team: "nuggets", colors: "linear-gradient(to bottom, #0E2240, #FEC524)" },
    { team: "pistons", colors: "linear-gradient(to bottom, #C8102E, #1D42BA)" },
    { team: "warriors", colors: "linear-gradient(to bottom, #1D428A, #FDB927)" },
    { team: "rockets", colors: "linear-gradient(to bottom, #8E2325, #C27E7E)" },
    { team: "pacers", colors: "linear-gradient(to bottom, #002D62, #FDBB30)" },
    { team: "clippers", colors: "linear-gradient(to bottom, #C8102E, #1D428A)" },
    { team: "lakers", colors: "linear-gradient(to bottom, #552583, #FDB927)" },
    { team: "grizzlies", colors: "linear-gradient(to bottom, #5D76A9, #12173F)" },
    { team: "heat", colors: "linear-gradient(to bottom, #98002E, #F9A01B)" },
    { team: "bucks", colors: "linear-gradient(to bottom, #00471B, #EEE1C6)" },
    { team: "timberwolves", colors: "linear-gradient(to bottom, #0C2340, #236192)" },
    { team: "pelicans", colors: "linear-gradient(to bottom, #0C2340, #C8102E)" },
    { team: "knicks", colors: "linear-gradient(to bottom, #006BB6, #F58426)" },
    { team: "thunder", colors: "linear-gradient(to bottom, #007AC1, #EF3B24)" },
    { team: "magic", colors: "linear-gradient(to bottom, #0077C0, #C4CED4)" },
    { team: "sixers", colors: "linear-gradient(to bottom, #006BB6, #ED174C)" },
    { team: "suns", colors: "linear-gradient(to bottom, #1D1160, #E56020)" },
    { team: "blazers", colors: "linear-gradient(to bottom, #E03A3E, #000000)" },
    { team: "kings", colors: "linear-gradient(to bottom, #5A2D81, #63727A)" },
    { team: "spurs", colors: "linear-gradient(to bottom, #000000, #C4CED4)" },
    { team: "raptors", colors: "linear-gradient(to bottom, #CE1141, #000000)" },
    { team: "jazz", colors: "linear-gradient(to bottom, #002B5C, #00471B)" },
    { team: "wizards", colors: "linear-gradient(to bottom, #002B5C, #E31837)" }
  ];

  useEffect(() => {
      async function fetchTeamAndPlayers() {
          const teamResponse = await fetch(`https://nbadle.onrender.com/teams/${teamId}`);
          const teamData = await teamResponse.json();
          setTeam(teamData.team);

          const playerResponse = await fetch(`https://nbadle.onrender.com/teams/${teamId}/players`);
          const playerData = await playerResponse.json();

          if (playerOption === 'Current Players') {
              playerData.players = playerData.players.filter(player => player.active === true);
          } else if (playerOption === 'Past Players') {
              playerData.players = playerData.players.filter(player => player.active === false);
          }

          setPlayers(playerData.players);

          const teamColor = teamColorSchemas.find(schema => schema.team === teamData.team.full_name.toLowerCase())?.colors;
          setTeamColor(teamColor || '');

          setLoading(false);
      }

      fetchTeamAndPlayers();
  }, [teamId, playerOption]);

  return (
      <div className='team-container' style={{ background: teamColor }}>
          {loading ? (
              <div className='team'>
                  <p className='loading'>Loading...</p>
              </div>
          ) : (
              <div className='team-content-container'>
                  <div className='team-info-container'>
                    <div className='team-primary-info'>
                      <h1 className='team-name'>{team.city} {team.full_name.charAt(0).toUpperCase() + team.full_name.slice(1)}</h1>
                      <img src={team.logo_url} alt={team.full_name} className='team-logo-image' />
                    </div>
                    <div className='team-details'>
                        <p>Conference: {team.conference}</p>
                        <p>Head Coach: {team.head_coach}</p>
                        <p>Associate Coaches: {team.associate_coach?.join(', ')}</p>
                        <p>Assistant Coaches: {team.assistant_coach?.join(', ')}</p>
                    </div>
                  </div>
                  <div className='team-player-list-container'>
                      <div className='team-player-list-header'>
                        <select className='player-filter-dropdown' value={playerOption} onChange={(e) => setPlayerOption(e.target.value)}>
                          <option value='All'>All Players</option>
                          <option value='Current Players'>Current Players</option>
                          <option value='Past Players'>Past Players</option>
                        </select>
                      </div>
                      <ul className='team-player-list'>
                          {players.map(player => (
                              <li key={player.id}>
                                  <Link to={`/players/${player.id}`} className='team-player-card'>
                                      <img src={player.image_url} alt={player.first_name} className='player-image' />
                                      <p>{player.first_name} {player.last_name}</p>
                                  </Link>
                              </li>
                          ))}
                      </ul>
                  </div>
              </div>
          )}
      </div>
  );
}

export default Team;
