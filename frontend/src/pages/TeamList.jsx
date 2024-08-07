import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import '../styles/TeamList.css';

function TeamList() {

    const [teams, setTeams] = useState([]);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        async function fetchTeams() {
            const response = await fetch('http://localhost:5000/teams');
            const data = await response.json();
            setTeams(data.teams);
            setLoading(false);
        }

        fetchTeams();
    }, []);

    const image_base_url = 'https://cdn.nba.com/logos/nba/';

    return (
        <div className='team-list-container'>
            <h1>Teams</h1>
            {loading ? (
                <p>Loading...</p>
            ) : (
                <ul className='team-list'>
                {teams.map((team) => (
                    <Link to={`/teams/${team.id}`} key={team.id} className='team-card'>
                        <img src={`${image_base_url}${team.id}/global/L/logo.svg`} alt={team.name} />
                        <p>{team.name}</p>
                    </Link>
                ))}
                </ul>
            )}
        </div>
    );
}

export default TeamList;