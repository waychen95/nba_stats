import '../styles/Guess.css';
import { useState, useEffect } from 'react';
import PlayerCard from '../components/PlayerCard';
import Loading from '../components/Loading';
import Modal from '../components/Modal';
import { Link } from 'react-router-dom';

const BASE_URL = import.meta.env.VITE_BASE_URL || 'http://localhost:3000';

function HardMode() {
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
    const [showModal, setShowModal] = useState(false);

    useEffect(() => {
        async function fetchPlayers() {
            const response = await fetch(`${BASE_URL}/guess_players`);
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
            setTries((tries) => tries + 1);
            setTimeout(() => setShowModal(true), 2500);
            setTimeout(() => setBrightness(1), 2500);
        } else {
            setCorrect(false);
            setIncorrectPlayers([...incorrectPlayers, guessPlayer]);
            if (brightness < 0.8) {
                setBrightness(brightness + 0.02);
            }

            setTries((tries) => tries + 1);
        }

        setSearch('');
        setDropdownLocked(false); // Unlock dropdown after guessing
    };

    const closeModal = () => {
        setShowModal(false);
    };

    return (
        <div className='guess-container'>
            {loading ? (
                <div className='player'>
                    <Loading />
                </div>
            ) : (
                <div className='player'>
                    <img src={correctPlayer.image_url} alt={`${correctPlayer.first_name} ${correctPlayer.last_name}`} style={{ filter: `brightness(${brightness}) contrast(100%)` }} className={correct ? 'correct-image' : 'incorrect-image'} />
                    <div className='player-info'>
                        <h2>Who is this player?</h2>
                        <Link to={`/players/${correctPlayer.id}`}/>
                    </div>
                    <div className='search-bar guess-search-bar'>
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
                                    {searchResults.map((player, index) => (
                                        <li
                                            key={`${player.id}-${index}`}
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
            {showModal && (
                <Modal 
                    correctPlayer={correctPlayer} 
                    tries={tries} 
                    onClose={closeModal} 
                />
            )}
            <div className='incorrect-players'>
                {incorrectPlayers.slice().reverse().map((player) => (
                    <PlayerCard key={player.id} player={player} correctPlayer={correctPlayer} />
                ))}
            </div>
        </div>
    );
}

export default HardMode;