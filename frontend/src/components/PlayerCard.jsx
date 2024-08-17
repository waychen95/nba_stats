import { useState, useEffect } from 'react';
import '../styles/PlayerCard.css';

function PlayerCard( { player, correctPlayer } ) {
    
    const [correctTeam, setCorrectTeam] = useState(false);
    const [correctPosition, setCorrectPosition] = useState(false);
    const [correctHeight, setCorrectHeight] = useState(false);
    const [correctConference, setCorrectConference] = useState(false);
    const [correctNumber, setcorrectNumber] = useState(false);
    const [numberHigh, setNumberHigh] = useState('');
    const [heightHigh, setHeightHigh] = useState('');
    const [partialPosition, setPartialPosition] = useState(false);

    useEffect(() => {
        compareEachInfo(player, correctPlayer);
    }, [player, correctPlayer]);

    const compareEachInfo = (player, correctPlayer) => {

        if (player.team_name === correctPlayer.team_name) {
            setCorrectTeam(true);
        }
        
        if (player.position === correctPlayer.position) {
            setCorrectPosition(true);
            setPartialPosition(false);
        } else if (correctPlayer.position.includes(player.position) || player.position.includes(correctPlayer.position)) {
            setPartialPosition(true);
        } else {
            setPartialPosition(false);
        }

        if (player.feet === correctPlayer.feet && player.inches === correctPlayer.inches) {
            setCorrectHeight(true);
            setHeightHigh('');
        } else if (player.feet > correctPlayer.feet) {
            setHeightHigh('arrow_downward');
        } else if (player.feet === correctPlayer.feet && player.inches > correctPlayer.inches) {
            setHeightHigh('arrow_downward');
        } else {
            setHeightHigh('arrow_upward');
        }

        if (player.team_conference === correctPlayer.team_conference) {
            setCorrectConference(true);
        }

        if (player.number === correctPlayer.number) {
            setcorrectNumber(true);
            setNumberHigh('');
        } else if (player.number > correctPlayer.number) {
            setNumberHigh('arrow_downward');
        } else {
            setNumberHigh('arrow_upward');
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
                <div className={`player-guess-info info-3 ${correctPosition ? 'correct-position' : 'incorrect'} ${partialPosition ? 'partial-position' : ''}`}>
                    <label>Position</label>
                    <p>{player.position}</p>
                </div>
                <div className={`player-guess-info info-4 ${correctHeight ? 'correct-height' : 'incorrect'}`}>
                    <label>Height <span class="material-symbols-outlined">{heightHigh}</span></label>
                    <p>{player.feet}'{player.inches}"</p>
                </div>
                <div className={`player-guess-info info-5 ${correctConference ? 'correct-conference' : 'incorrect'}`}>
                    <label>Conference</label>
                    <p>{player.team_conference}</p>
                </div>
                <div className={`player-guess-info info-6 ${correctNumber ? 'correct-number' : 'incorrect'}`}>
                    <label>Jersey Number <span class="material-symbols-outlined">{numberHigh}</span></label>
                    <p>{player.number}</p>
                </div>
            </div>
        </div>
    );
    
}

export default PlayerCard;