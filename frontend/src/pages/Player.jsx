import { useState, useEffect } from 'react';
import { useParams } from 'react-router-dom';
import '../styles/Player.css';
import PlayerStats from '../components/PlayerStats';
import Loading from '../components/Loading';
import { Link } from 'react-router-dom';

const BASE_URL = import.meta.env.VITE_BASE_URL || 'http://localhost:3000';

function Player() {

    const [player, setPlayer] = useState({});
    const [loading, setLoading] = useState(true);
    const [team, setTeam] = useState({});
    const [cmHeight, setCmHeight] = useState(0);
    const [kgWeight, setKgWeight] = useState(0);
    const [teamColor, setTeamColor] = useState('');

    const { id } = useParams();

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
        async function fetchPlayerAndTeam() {
            const response = await fetch(`${BASE_URL}/players/${id}`);
            const data = await response.json();
            setPlayer(data.player);

            setCmHeight((data.player.feet * 30.48) + (data.player.inches * 2.54));
            setKgWeight(data.player.weight * 0.453592);

            const teamResponse = await fetch(`${BASE_URL}/teams/${data.player.team_id}`);
            const teamData = await teamResponse.json();
            setTeam(teamData.team);

            const teamColor = teamColorSchemas.find(teamColor => teamColor.team === teamData.team.full_name.toLowerCase())?.colors;
            setTeamColor(teamColor);

            setLoading(false);
        }

        fetchPlayerAndTeam();
    }, [id]);

    return (
        <div className='player-container' style={{ background: teamColor }}>
            {loading ? (
                <div className='player' style={{ margin: 'auto' }}>
                    <Loading />
                </div>
            ) : (
                <div className='player-content-container'>
                    <div className='player-info-container'>
                        <Link to={`/teams/${team.id}`} className='team-link'>
                            <img src={team.logo_url} alt={team.full_name} className='team-logo'></img>
                        </Link>
                        <div className='player-primary-info'>
                            <h1 className='player-number'>#{player.number}</h1>
                            <img src={player.image_url} alt={`${player.first_name} ${player.last_name}`} className='player-image'></img>
                            <div className='player-identity'>
                                <div className='player-name'>
                                    <h1 className='first-name'>{player.first_name} {player.last_name}</h1>
                                </div>
                                <h3 className='team-position'>{team.full_name.charAt(0).toUpperCase() + team.full_name.slice(1)} | {player.position}</h3>
                            </div>
                        </div>
                        <div className='player-second-info'>
                            <p>Height: {player.feet}'{player.inches} / {cmHeight.toFixed(1)} cm</p>
                            <p>Weight (lbs): {player.weight} / {kgWeight.toFixed(1)} kg</p>
                            <p>Country: {player.country}</p>
                        </div>
                        <div className='player-bio'>
                            <h2>Professional Career</h2>
                            <p>{player.professional_bio}</p>
                            <h2>Before NBA</h2>
                            <p>{player.before_nba_bio}</p>
                            <h2>Personal Life</h2>
                            <p>{player.personal_bio}</p>
                        </div>
                    </div>
                    <PlayerStats playerId={id} teamName={team.full_name} />
                </div>
            )}  
        </div>
    );
}

export default Player;