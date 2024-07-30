import { useState, useEffect } from 'react';

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

    return (
        <div>
        <h1>Teams</h1>
        {loading ? (
            <p>Loading...</p>
        ) : (
            <ul>
            {teams.map((team) => (
                <li key={team.id}>
                {team.name}
                </li>
            ))}
            </ul>
        )}
        </div>
    );
}

export default TeamList;