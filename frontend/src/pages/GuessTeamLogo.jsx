import '../styles/Guess.css';
import { useState, useEffect } from 'react';
import TeamLogoPlayerCard from '../components/TeamLogoPlayerCard';
import { Link } from 'react-router-dom';
import '../styles/GuessTeamLogo.css';

function GuessTeamLogo() {
    const [correctPlayer, setCorrectPlayer] = useState({});
    const [allPlayers, setAllPlayers] = useState([]);
    const [pastTeams, setPastTeams] = useState([]);
    const [loading, setLoading] = useState(true);
    const [search, setSearch] = useState('');
    const [searchResults, setSearchResults] = useState([]);
    const [showDropdown, setShowDropdown] = useState(false);
    const [dropdownLocked, setDropdownLocked] = useState(false);
    const [correct, setCorrect] = useState(false);
    const [incorrectPlayers, setIncorrectPlayers] = useState([]);
    const [tries, setTries] = useState(0);

    useEffect(() => {
        async function fetchTeam(abbr) {
            try {
                const response = await fetch(`http://localhost:5000/teams/abbr/${abbr}`);
                if (!response.ok) {
                    throw new Error(`Failed to fetch team: ${response.statusText}`);
                }
                const data = await response.json();
                return data.team;
            } catch (error) {
                console.error('Error fetching team:', error);
                return null; // Handle the error gracefully
            }
        }

        async function fetchPlayers() {
            try {
                const response = await fetch('http://localhost:5000/players');
                const data = await response.json();
                const playerList = data.players;

                setAllPlayers(playerList);

                // Pick a random player for the guessing game
                const randomPlayer = playerList[Math.floor(Math.random() * playerList.length)];
                setCorrectPlayer(randomPlayer);

                console.log('Random player:', randomPlayer);

                const playerPastTeams = randomPlayer.past_teams;

                // Fetch logos for each team in the player's past teams
                const teams = [];
                for (let i = 0; i < playerPastTeams.length; i++) {
                    const current = playerPastTeams[i];
                    if (current === 'TOT') {
                        continue;
                    }
                    const team = await fetchTeam(current);
                    if (!team) {
                        continue;
                    }
                    teams.push(team); // Add each team to the array
                }

                setPastTeams(teams); // Set all teams at once after the loop ends
                setLoading(false);
            } catch (error) {
                console.error('Error fetching players:', error);
            }
        }

        setCorrect(false);
        fetchPlayers();  // Ensure this only runs once by having an empty dependency array
    }, []); // Empty array to ensure this runs only once on component mount

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
    }

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
        } else {
            setCorrect(false);
            setIncorrectPlayers([...incorrectPlayers, guessPlayer]);
        }

        setSearch('');
        setDropdownLocked(false); // Unlock the dropdown after a guess
    };

    return (
        <div className='guess-container'>
            {loading ? (
                <div className='player'>
                    <p className='loading'>Loading...</p>
                </div>
            ) : (
                <div className='player'>
                    <h2>Guess the Player</h2>
                    <div className='past-teams'>
                        {pastTeams.map((team) => (
                            <img key={team.id} src={team.logo_url} alt={team.name} />
                        ))}
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
                    <TeamLogoPlayerCard key={player.id} player={player} correctPlayer={correctPlayer} />
                ))}
            </div>
        </div>
    );
}

export default GuessTeamLogo;
