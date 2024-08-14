import React, { useState, useEffect } from 'react';
import { Link, useParams } from 'react-router-dom';
import '../styles/Team.css';

function Team() {
  const { teamId } = useParams();

    const [team, setTeam] = useState({});

    const [loading, setLoading] = useState(true);

    const [players, setPlayers] = useState([]);

    const [playerLoading, setPlayerLoading] = useState(true);

    const [profileLoading, setProfileLoading] = useState(true);

    useEffect(() => {
        async function fetchTeam() {
            const response = await fetch(`http://localhost:5000/teams/${teamId}`);
            const data = await response.json();
            setTeam(data.team);
            setLoading(false);
        }

        fetchTeam();
        getProfile();
    }, [teamId]);

    const getPlayers = async () => {
        const response = await fetch(`http://localhost:5000/teams/${teamId}/players`);
        const data = await response.json();
        setPlayers(data.players);
        setPlayerLoading(false);
        setProfileLoading(true);
    }

    const getProfile = () => {
      setPlayerLoading(true);
      setProfileLoading(false);
    }

  return (
    <div className='team-container'>
        {loading ? (
          <div className='team'>
            <p className='loading'>Loading...</p>
          </div>
        ) : (
          <div className='team'>
            <h2>{team.city} {team.full_name}</h2>
            <img src={team.logo_url} alt={team.name} />
            <div>
              <button className='button' onClick={getProfile}>Profile</button>
              <button className='button' onClick={getPlayers}>Players</button>
            </div>
          </div>
        )}
        {profileLoading ? (
          <p>Loading...</p>
        ) : (
          <div className='team-profile'>
            <h3>Profile</h3>
            <p>Conference: {team.conference}</p>
            <p>Head Coach: {team.head_coach}</p>
            <div>
              <p>Associate Coach:</p>
              <ul>
                {team.associate_coach && team.associate_coach.map((coach, index) => (
                  <li key={index}>{coach}</li>
                ))}
              </ul>
            </div>
            <div>
              <p>Assistant Coach:</p>
              <ul>
                {team.assistant_coach && team.assistant_coach.map((coach, index) => (
                  <li key={index}>{coach}</li>
                ))}
              </ul>
            </div>
          </div>
        )}
        {playerLoading ? (
          <p>Loading...</p>
        ) : (
          <div className='team-player-list-container'>
            <h3>Players</h3>
            <ul className='team-player-list'>
              {players.map((player) => (
                <li key={player.id}>
                  <Link to={`/players/${player.id}`}>
                    <div className='team-player-card'>
                      <img src={player.image_url} alt={player.name} />
                      <p>{player.first_name} {player.last_name}</p>
                    </div>
                  </Link>
                </li>
              ))}
            </ul>
          </div>
        )}
    </div>
  );
}

export default Team;