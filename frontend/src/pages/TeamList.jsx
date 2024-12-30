import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import '../styles/TeamList.css';

function TeamList() {

    const [teams, setTeams] = useState([]);
    const [loading, setLoading] = useState(true);
    const [order, setOrder] = useState('asc');
    const [conference, setConference] = useState('');

    const conference_list = ['Eastern', 'Western'];

    useEffect(() => {
        async function fetchTeams() {
            let url = `http://localhost:5000/teams?order=${order}`;
            if (conference) {
                url += `&conference=${conference}`;
            }
            const response = await fetch(url);
            const data = await response.json();
            setTeams(data.teams);
            setLoading(false);
        }

        fetchTeams();
    }, [order, conference]);

    const image_base_url = 'https://cdn.nba.com/logos/nba/';

    return (
        <div className='team-list-container'>
            <h1>Teams</h1>
            <div className='team-list-dropdowns'>
            <div className='dropdown-name'>
            <label>Order by name:</label>
            <select value={order} onChange={(e) => setOrder(e.target.value)}>
                <option value='asc'>Ascending</option>
                <option value='desc'>Descending</option>
            </select>
            </div>
            <div className='dropdown-conference'>
            <label>Filter by conference:</label>
            <select value={conference} onChange={(e) => setConference(e.target.value)}>
                <option value=''>All Teams</option>
                {conference_list.map((conference) => (
                <option key={conference} value={conference}>
                    {conference}
                </option>
                ))}
            </select>
            </div>
        </div>
            {loading ? (
                <div className='team-list'>
                    <p className='loading'>Loading...</p>
                </div>
            ) : (
                <ul className='team-list'>
                {teams.map((team) => (
                    <Link to={`/teams/${team.id}`} key={team.id} className='team-card'>
                        <img src={`${image_base_url}${team.id}/global/L/logo.svg`} alt={team.name} />
                        <p>{team.full_name}</p>
                    </Link>
                ))}
                </ul>
            )}
        </div>
    );
}

export default TeamList;