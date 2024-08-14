import { useState, useEffect } from 'react';
import '../styles/PlayerCard.css';

function PlayerCard( { player, correctPlayer } ) {
    
    const [correctTeam, setCorrectTeam] = useState(false);
    const [correctPosition, setCorrectPosition] = useState(false);
    const [correctHeight, setCorrectHeight] = useState(false);
    const [correctConference, setCorrectConference] = useState(false);
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

        if (player.team_conference === correctPlayer.team_conference) {
            setCorrectConference(true);
        }

        if (player.country === correctPlayer.country) {
            setCorrectCountry(true);
        }
    }

    return (
        <div className='guessed-player-cards-div'>
            <div className='guessed-player-cards'>
                <img src={player.image_url} alt={player.name} />
                <div className={`player-guess-info info-1 `}>
                    <p>{player.first_name} {player.last_name}</p>
                </div>
                <div className={`player-guess-info info-2 ${correctTeam ? 'correct-team' : 'incorrect'}`}>
                    <label>Team</label>
                    <p>{player.team_name}</p>
                </div>
                <div className={`player-guess-info info-3 ${correctPosition ? 'correct-position' : 'incorrect'}`}>
                    <label>Position</label>
                    <p>{player.position}</p>
                </div>
                <div className={`player-guess-info info-4 ${correctHeight ? 'correct-height' : 'incorrect'}`}>
                    <label>Height</label>
                    <p>{player.feet}'{player.inches}"</p>
                </div>
                <div className={`player-guess-info info-5 ${correctConference ? 'correct-conference' : 'incorrect'}`}>
                    <label>Conference</label>
                    <p>{player.team_conference}</p>
                </div>
                <div className={`player-guess-info info-6 ${correctCountry ? 'correct-country' : 'incorrect'}`}>
                    <label>Country</label>
                    <p>{player.country}</p>
                </div>
            </div>
        </div>
    );
    
}

export default PlayerCard;