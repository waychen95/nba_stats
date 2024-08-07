import React, { useState, useEffect } from 'react';
import { useParams } from 'react-router-dom';
import '../styles/Team.css';

function Team() {
  const { teamId } = useParams();

    const [team, setTeam] = useState({});

    const [loading, setLoading] = useState(true);

    useEffect(() => {
        async function fetchTeam() {
            const response = await fetch(`http://localhost:5000/teams/${teamId}`);
            const data = await response.json();
            setTeam(data.team);
            setLoading(false);
        }

        fetchTeam();
    }, [teamId]);

    const image_base_url = 'https://cdn.nba.com/logos/nba/';

  return (
    <div className='team-container'>
        {loading ? (
            <p>Loading...</p>
        ) : (
          <div className='team'>
            <img src={`${image_base_url}${team.id}/global/L/logo.svg`} alt={team.name} />
            <h2>{team.name}</h2>
            <p>URL: {team.url}</p>
          </div>
        )}
    </div>
  );
}

export default Team;