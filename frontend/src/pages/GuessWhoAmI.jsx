import { useState, useEffect } from 'react';
import TeamLogoPlayerCard from '../components/TeamLogoPlayerCard';
import Loading from '../components/Loading';
import Modal from '../components/Modal';
import '../styles/GuessWhoAmI.css';

const BASE_URL = import.meta.env.VITE_BASE_URL || 'http://localhost:3000';

function GuessWhoAmI() {
    const [correctPlayer, setCorrectPlayer] = useState({});
    const [allPlayers, setAllPlayers] = useState([]);
    const [loading, setLoading] = useState(true);
    const [search, setSearch] = useState('');
    const [searchResults, setSearchResults] = useState([]);
    const [showDropdown, setShowDropdown] = useState(false);
    const [dropdownLocked, setDropdownLocked] = useState(false);
    const [correct, setCorrect] = useState(false);
    const [incorrectPlayers, setIncorrectPlayers] = useState([]);
    const [tries, setTries] = useState(0);
    const [bio, setBio] = useState("");
    const [hint, setHint] = useState(false);
    const [maxTries, setMaxTries] = useState(4);
    const [secondHint, setSecondHint] = useState(8);
    const [showModal, setShowModal] = useState(false);

    useEffect(() => {
        async function fetchPlayers() {
            try {
                const response = await fetch(`${BASE_URL}/well_known_players`);
                const data = await response.json();
                let playerList = data.players;

                playerList = playerList.filter(player => player.professional_bio !== 'No professional bio available' && player.before_nba_bio !== "No before NBA bio available" && player.personal_bio !== "No personal bio available");

                playerList = playerList.filter(player => player.professional_bio !== null && player.before_nba_bio !== null && player.personal_bio !== null);

                setAllPlayers(playerList);

                // Pick a random player for the guessing game
                const randomPlayer = playerList[Math.floor(Math.random() * playerList.length)];
                setCorrectPlayer(randomPlayer);
                const playerBio = reformatBio(randomPlayer);
                setBio(playerBio);
                setLoading(false);
            } catch (error) {
                console.error('Error fetching players:', error);
            }
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
    }, [search, allPlayers, incorrectPlayers, dropdownLocked, tries]);

    const handleSearchChange = (e) => {
        setSearch(e.target.value);
        setDropdownLocked(false); // Unlock dropdown when the input changes
    }

    const handlePlayerSelect = (player) => {
        setSearch(player.first_name + ' ' + player.last_name);
        setShowDropdown(false); // Close the dropdown
        setDropdownLocked(true); // Lock the dropdown to prevent it from showing immediately after selection
    };

    const reformatBio = (player) => {
        const firstName = player.first_name;
        const lastName = player.last_name;
        const fullName = `${firstName} ${lastName}`;
        const professional_bio = `<h2>Professional Career:</h2><p>${player.professional_bio}</p>`;
        const before_nba_bio = `<h2>Before NBA:</h2><p>${player.before_nba_bio}</p>`;
        const personal_bio = `<h2>Personal Life:</h2><p>${player.personal_bio}</p>`;
        const playerBio = `${professional_bio}${before_nba_bio}${personal_bio}`;
    
        const reformatBio = playerBio
            .replace(new RegExp(`\\b${firstName}\\b`, 'gi'), 'XYZ')
            .replace(new RegExp(`\\b${lastName}\\b`, 'gi'), 'XYZ')
            .replace(new RegExp(`\\b${fullName}\\b`, 'gi'), 'XYZ')
            .replace(new RegExp(`\\b${fullName.toLowerCase()}\\b`, 'gi'), 'XYZ')
            .replace(/@\w+/g, '@XYZ');
    
        return reformatBio;
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
            setBio(correctPlayer.bio);
            setIncorrectPlayers([...incorrectPlayers, guessPlayer]);
            setTimeout(() => setShowModal(true), 2000);
        } else {
            setCorrect(false);
            setIncorrectPlayers([...incorrectPlayers, guessPlayer]);
        }

        setTries((tries) => tries + 1);

        setSearch('');
        setDropdownLocked(false); // Unlock the dropdown after a guess
    };

    return (
        <div className="guess-who-am-i">
            {loading ? (
                <div className='player'>
                    <Loading />
                </div>
            ) : (
                <div className='player'>
                    <div className='guess-whoami-player'>
                        <p dangerouslySetInnerHTML={{ __html: bio }} />
                    </div>
                    {hint && (
                        <div className='guess-whoami-hint'>
                            <p>First Hint: The team name of the player is: {correctPlayer.team_name}.</p>
                            {tries >= secondHint && (
                                <p>Second Hint: The first three letters of the player's first name are: {correctPlayer.first_name.slice(0, 3)}.</p>
                            )}
                        </div>
                    )}
                    {tries >= 1 && (
                        <div 
                            className={`hint ${tries >= maxTries ? 'hover-effect' : ''} ${tries >= maxTries ? '' : 'disabled'}`}
                            onClick={() => {
                                if (correct || tries < maxTries) {
                                    return;
                                }
                                setHint(hint => !hint);
                            }}
                        >
                            <p>Hint ({maxTries - tries > 0 ? maxTries - tries : 0})</p>
                        </div>                    
                    )}
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
            {showModal && (
                <Modal 
                    correctPlayer={correctPlayer} 
                    tries={tries} 
                    onClose={() => setShowModal(false)} 
                />
            )}
            <div className='incorrect-players'>
                {incorrectPlayers.slice().reverse().map((player) => (
                    <TeamLogoPlayerCard key={player.id} player={player} correctPlayer={correctPlayer} />
                ))}
            </div>
        </div>
    );
}

export default GuessWhoAmI;
