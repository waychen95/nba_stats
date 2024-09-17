import { useState, useEffect } from 'react';
import '../styles/TeamLogoPlayerCard.css';

function PlayerCard( { player, correctPlayer } ) {

    const [correct, setCorrect] = useState(false);
    

    useEffect(() => {
        compareEachInfo(player, correctPlayer);
    }, [player, correctPlayer]);

    const compareEachInfo = (player, correctPlayer) => {

        if (player.id === correctPlayer.id) {
            setCorrect(true);
        }
        
    }

    return (
        <div className='guessed-player-cards-div'>
            <div className={`guessed-player-cards ${correct ? 'correct-player' : 'incorrect-player'}`}>
                <img src={player.image_url} alt={player.name} />
                <div className={`player-guess-info info-1 ${correct ? 'correct-player' : 'incorrect-player'}`}>
                    <p>{player.first_name} {player.last_name}</p>
                </div>
            </div>
        </div>
    );
    
}

export default PlayerCard;