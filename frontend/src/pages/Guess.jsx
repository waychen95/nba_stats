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
    const [dropdownLocked, setDropdownLocked] = useState(false); // New state to control dropdown visibility
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
            const filteredResults = allPlayers.filter(player => {
                const fullName = `${player.first_name.toLowerCase()} ${player.last_name.toLowerCase()}`;
                return (
                    fullName.includes(search.toLowerCase()) &&
                    !incorrectPlayers.some(incorrectPlayer => incorrectPlayer.id === player.id) // Exclude guessed players
                );
            });
            setSearchResults(filteredResults);
            if (!dropdownLocked) {
                setShowDropdown(true); // Show the dropdown only if it's not locked
            }
        } else {
            setSearchResults([]);
            setShowDropdown(false);
        }

    }, [search, allPlayers, incorrectPlayers, dropdownLocked]);

    const handleSearchChange = (e) => {
        setSearch(e.target.value);
        setDropdownLocked(false); // Unlock dropdown when the input changes
    };

    const handlePlayerSelect = (player) => {
        setSearch(player.first_name + ' ' + player.last_name);
        setShowDropdown(false); // Close the dropdown
        setDropdownLocked(true); // Lock the dropdown to prevent it from showing immediately after selection
    };

    const compareGuessPlayer = () => {
        const guessPlayer = allPlayers.find(player => 
            `${player.first_name.toLowerCase()} ${player.last_name.toLowerCase()}` === search.toLowerCase()
        );
        if (!guessPlayer) {
            alert('Please enter a valid player name.');
            return;
        }

        if (guessPlayer.id === correctPlayer.id) {
            setCorrect(true);
            setIncorrectPlayers([...incorrectPlayers, guessPlayer]);
            setBrightness(1);
            setTries((tries) => tries + 1);
        } else {
            setCorrect(false);
            setIncorrectPlayers([...incorrectPlayers, guessPlayer]);
            if (brightness < 0.8) {
                setBrightness(brightness + 0.05);
            }

            setTries((tries) => tries + 1);
        }

        setSearch('');
        setDropdownLocked(false); // Unlock dropdown after guessing
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
                                onClick={() => !dropdownLocked && setShowDropdown(true)} // Prevent dropdown from showing if locked
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