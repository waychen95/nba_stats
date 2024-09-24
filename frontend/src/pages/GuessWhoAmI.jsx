import { useState, useEffect } from 'react';
import TeamLogoPlayerCard from '../components/TeamLogoPlayerCard';
import '../styles/GuessWhoAmI.css';

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

    useEffect(() => {
        async function fetchPlayers() {
            try {
                const response = await fetch('http://localhost:5000/players');
                const data = await response.json();
                let playerList = data.players;

                playerList = playerList.filter(player => player.bio !== 'No bio available' && player.image_url !== 'https://cdn.nba.com/headshots/nba/latest/260x190/1641794.png');

                setAllPlayers(playerList);

                // Pick a random player for the guessing game
                const randomPlayer = playerList[Math.floor(Math.random() * playerList.length)];
                setCorrectPlayer(randomPlayer);
                console.log('Random player:', randomPlayer);
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
        const fullName = `${firstName}${lastName}`;
        const playerBio = player.bio;
    
        // Replace the first and last name in the bio with 'XYZ'
        const reformatBio = playerBio
            .replace(new RegExp(`\\b${firstName}\\b`, 'gi'), 'XYZ') // \b ensures word boundary for exact match
            .replace(new RegExp(`\\b${lastName}\\b`, 'gi'), 'XYZ')
            .replace(new RegExp(`\\b${fullName}\\b`, 'gi'), 'XYZ')
            .replace(new RegExp(`\\b${fullName.toLowerCase()}\\b`, 'gi'), 'XYZ')
            .replace(/@\w+/g, '@XYZ');
    
        return reformatBio;
    }

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
        } else {
            setCorrect(false);
            setIncorrectPlayers([...incorrectPlayers, guessPlayer]);
        }

        setTries((tries) => tries + 1);
        
        console.log(tries);

        setSearch('');
        setDropdownLocked(false); // Unlock the dropdown after a guess
    };

    return (
        <div className="guess-who-am-i">
            {loading ? (
                <div className='player'>
                    <p className='loading'>Loading...</p>
                </div>
            ) : (
                <div className='player'>
                    <h2 id="guess-team-logo-title">{correct ? `Number of tries: ${tries}` : 'Who is this player?'}</h2>
                    <div className='guess-whoami-player'>
                        <p>{bio}</p>
                    </div>
                    {hint && (
                        <div className='hint'>
                            <p>Hint: The player's first name is {correctPlayer.first_name}.</p>
                        </div>
                    )}
                    {tries >= 3 && (
                        <div className='hint button' onClick={() => setHint(hint => !hint)}>Hint {3 - tries}</div>
                    )}
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
                    <TeamLogoPlayerCard key={player.id} player={player} correctPlayer={correctPlayer} />
                ))}
            </div>
        </div>
    );
}

export default GuessWhoAmI;
