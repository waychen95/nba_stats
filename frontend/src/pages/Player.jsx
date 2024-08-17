import { useState, useEffect } from 'react';
import { useParams } from 'react-router-dom';
import '../styles/Player.css';
import PlayerStats from '../components/PlayerStats';
import { Link } from 'react-router-dom';


function Player() {

    const [player, setPlayer] = useState({});
    const [loading, setLoading] = useState(true);

    const [team, setTeam] = useState({});

    const [profile, setProfile] = useState(true);
    const [stats, setStats] = useState(false);
    const [bio, setBio] = useState(false);

    const { id } = useParams();

    useEffect(() => {
        async function fetchPlayerAndTeam() {
            const response = await fetch(`http://localhost:5000/players/${id}`);
            const data = await response.json();
            setPlayer(data.player);

            const teamResponse = await fetch(`http://localhost:5000/teams/${data.player.team_id}`);
            const teamData = await teamResponse.json();
            setTeam(teamData.team);

            setLoading(false);
        }

        fetchPlayerAndTeam();
    }, [id]);

    return (
        <div className='player-container'>
            {loading ? (
                <div className='player'>
                    <p className='loading'>Loading...</p>
                </div>
            ) : (
                <div className='player'>
                    <h2>{player.first_name} {player.last_name} #{player.number}</h2>
                    <img src={player.image_url} alt={`${player.first_name} ${player.last_name}`} ></img>
                    <div className='player-info-buttons'>
                        <button className='button' onClick={() => { setProfile(true); setStats(false); setBio(false); }}>Profile</button>
                        <button className='button' onClick={() => { setProfile(false); setStats(true); setBio(false); }}>Stats</button>
                        <button className='button' onClick={() => { setProfile(false); setStats(false); setBio(true); }}>Bio</button>
                    </div>
                    {profile && (
                        <div className='player-info'>
                            <div className='player-info-team'>
                                <Link to={`/teams/${player.team_id}`}>
                                    <p>Team: {player.team_name}</p>
                                    <img src={team.logo_url} alt={team.name} />
                                </Link>
                            </div>
                            <p>Position: {player.position}</p>
                            <p>Height: {player.feet}'{player.inches}</p>
                            <p>Weight (lbs): {player.weight}</p>
                            <p>Country: {player.country}</p>
                        </div>
                    )}
                    {stats && <PlayerStats playerId={id} />}
                    {bio && (
                        <div className='player-bio'>
                            <p>{player.bio}</p>
                        </div>
                    )}
                </div>
            )}
        </div>
    );
}

export default Player;