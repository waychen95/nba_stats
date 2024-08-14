import '../styles/Guess.css';
import { useState, useEffect } from 'react';
import PlayerCard from '../components/PlayerCard';

function Guess() {
    const [correctPlayer, setCorrectPlayer] = useState({});
    const [allPlayers, setAllPlayers] = useState([]);
    const [loading, setLoading] = useState(true);
    const [search, setSearch] = useState('');
    const [searchResults, setSearchResults] = useState([]);
    const [showDropdown, setShowDropdown] = useState(false);
    const [correct, setCorrect] = useState(false);
    const [incorrectPlayers, setIncorrectPlayers] = useState([]);
    const [brightness, setBrightness] = useState(0);
    const [tries, setTries] = useState(0);

    useEffect(() => {
        async function fetchPlayers() {
            const response = await fetch('http://localhost:5000/players');
            const data = await response.json();
            const playerList = data.players;

            setAllPlayers(playerList);

            // Pick a random player for the guessing game
            const randomPlayer = playerList[Math.floor(Math.random() * playerList.length)];
            setCorrectPlayer(randomPlayer);
            setLoading(false);
        }

        setCorrect(false);

        fetchPlayers();
    }, []);

    useEffect(() => {
        if (search) {
            const filteredResults = allPlayers.filter(player => 
                (player.first_name.toLowerCase().includes(search.toLowerCase()) ||
                player.last_name.toLowerCase().includes(search.toLowerCase())) &&
                !incorrectPlayers.some(incorrectPlayer => incorrectPlayer.id === player.id) // Exclude guessed players
            );
            setSearchResults(filteredResults);
            setShowDropdown(true);
        } else {
            setSearchResults([]);
            setShowDropdown(false);
        }

    }, [search, allPlayers, incorrectPlayers]);

    const handleSearchChange = (e) => {
        setSearch(e.target.value);
    };

    const handlePlayerSelect = (player) => {
        setSearch(player.first_name + ' ' + player.last_name);
        setShowDropdown(false);
    };

    const compareGuessPlayer = () => {
        let guessPlayer = allPlayers.find(player => player.first_name + ' ' + player.last_name === search);
        if (!guessPlayer) {
            alert('Please enter a valid player name.');
            return;
        }

        if (guessPlayer.id === correctPlayer.id) {
            setCorrect(true);
            setIncorrectPlayers([...incorrectPlayers, guessPlayer]);
            setBrightness(1);
        } else {
            setCorrect(false);
            setIncorrectPlayers([...incorrectPlayers, guessPlayer]);
            if (brightness < 1) {
                setBrightness(brightness + 0.1);
            }

            setTries((tries) => tries + 1);
        }

        console.log(tries);

        setSearch('');

    };


    return (
        <div className='guess-container'>
            {loading ? (
                <div className='player'>
                    <p className='loading'>Loading...</p>
                </div>
            ) : (
                <div className='player'>
                    <img src={correctPlayer.image_url} alt={`${correctPlayer.first_name} ${correctPlayer.last_name}`} style={{ filter: `brightness(${brightness}) contrast(100%)` }} className={correct ? 'correct-image' : 'incorrect-image'} />
                    <div className='player-info'>
                        <h2>{correct ? `Number of tries: ${tries}` : 'Who is this player?'}</h2>
                        <button className='button' onClick={() => window.location.reload()} style={{display: `${correct ? 'block' : 'none'}`}}>Player Again!</button>
                    </div>
                    <div className='search-bar'>
                        <div className='search-dropdown-div'>
                            <input
                                type='text'
                                placeholder='Enter player name...'
                                value={search}
                                onChange={handleSearchChange}
                                onClick={() => setShowDropdown(true)}
                                disabled={correct}
                            />
                            {showDropdown && searchResults.length > 0 && (
                                <ul className='search-dropdown'>
                                    {searchResults.map((player) => (
                                        <li
                                            key={player.id}
                                            onClick={() => handlePlayerSelect(player)}
                                        >
                                            {player.first_name} {player.last_name}
                                        </li>
                                    ))}
                                </ul>
                            )}
                        </div>
                        <button className='guess-button' onClick={compareGuessPlayer} disabled={correct}>Guess</button>
                    </div>
                </div>
            )}
            <div className='incorrect-players'>
                {incorrectPlayers.slice().reverse().map((player) => (
                    <PlayerCard key={player.id} player={player} correctPlayer={correctPlayer} />
                ))}
            </div>
        </div>
    );
}

export default Guess;
