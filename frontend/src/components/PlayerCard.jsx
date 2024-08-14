import { useState, useEffect } from 'react';
import '../styles/PlayerCard.css';

function PlayerCard( { player, correctPlayer } ) {
    
    const [correctTeam, setCorrectTeam] = useState(false);
    const [correctPosition, setCorrectPosition] = useState(false);
    const [correctHeight, setCorrectHeight] = useState(false);
    const [correctWeight, setCorrectWeight] = useState(false);
    const [correctCountry, setCorrectCountry] = useState(false)

    useEffect(() => {
        compareEachInfo(player, correctPlayer);
    }, [player, correctPlayer]);

    const compareEachInfo = (player, correctPlayer) => {
        if (player.team_name === correctPlayer.team_name) {
            setCorrectTeam(true);
        }
        
        if (player.position === correctPlayer.position) {
            setCorrectPosition(true);
        }

        if (player.feet === correctPlayer.feet && player.inches === correctPlayer.inches) {
            setCorrectHeight(true);
        }

        if (player.weight === correctPlayer.weight) {
            setCorrectWeight(true);
        }

        if (player.country === correctPlayer.country) {
            setCorrectCountry(true);
        }
    }

    return (
        <div className='player-card'>
            <img src={player.image_url} alt={player.name} />
            <div className={`player-guess-info`}>
                <p>{player.first_name} {player.last_name}</p>
            </div>
            <div className={`player-guess-info ${correctTeam ? 'correct-team' : 'incorrect'}`}>
                <p>{player.team_name}</p>
            </div>
            <div className={`player-guess-info ${correctPosition ? 'correct-position' : 'incorrect'}`}>
                <p>{player.position}</p>
            </div>
            <div className={`player-guess-info ${correctHeight ? 'correct-height' : 'incorrect'}`}>
                <p>{player.feet}'{player.inches}</p>
            </div>
            <div className={`player-guess-info ${correctWeight ? 'correct-weight' : 'incorrect'}`}>
                <p>{player.weight}</p>
            </div>
            <div className={`player-guess-info ${correctCountry ? 'correct-country' : 'incorrect'}`}>
                <p>{player.country}</p>
            </div>
        </div>
    );
}

export default PlayerCard;