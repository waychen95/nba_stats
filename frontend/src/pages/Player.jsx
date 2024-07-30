import { useState, useEffect } from 'react';
import { useParams } from 'react-router-dom';


function Player() {

    const [player, setPlayer] = useState({});
    const [loading, setLoading] = useState(true);

    const { id } = useParams();

    useEffect(() => {
        async function fetchPlayer() {
            const response = await fetch(`http://localhost:5000/players/${id}`);
            const data = await response.json();
            setPlayer(data.player);
            setLoading(false);
        }

        fetchPlayer();
    }, [id]);

    return (
        <div>
            <h1>Player</h1>
            {loading ? (
                <p>Loading...</p>
            ) : (
                <div>
                    <h2>{player.first_name} {player.last_name}</h2>
                    <p>Team: {player.team_name}</p>
                    <p>Position: {player.position}</p>
                </div>
            )}
        </div>
    );
}

export default Player;