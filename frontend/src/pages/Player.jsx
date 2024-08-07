import { useState, useEffect } from 'react';
import { useParams } from 'react-router-dom';
import '../styles/Player.css';


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
        <div className='player-container'>
            {loading ? (
                <p>Loading...</p>
            ) : (
                <div className='player'>
                    <h2>{player.first_name} {player.last_name}</h2>
                    <img src={player.image_url} alt={`${player.first_name} ${player.last_name}`} ></img>
                    <div className='player-info'>
                        <p>Team: {player.team_name}</p>
                        <p>Position: {player.position}</p>
                        <p>Height: {player.feet}'{player.inches}</p>
                        <p>Weight (lbs): {player.weight}</p>
                        <p>Country: {player.country}</p>
                    </div>
                </div>
            )}
        </div>
    );
}

export default Player;