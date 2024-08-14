import '../styles/Guess.css';
import { useState, useEffect } from 'react';
import PlayerCard from '../components/PlayerCard';

function Guess() {
    const [correctPlayer, setCorrectPlayer] = useState({});
    const [guessPlayer, setGuessPlayer] = useState('');
    const [allPlayers, setAllPlayers] = useState([]);
    const [loading, setLoading] = useState(true);
    const [search, setSearch] = useState('');
    const [searchResults, setSearchResults] = useState([]);
    const [showDropdown, setShowDropdown] = useState(false);
    const [correct, setCorrect] = useState(false);
    const [incorrectPlayers, setIncorrectPlayers] = useState([]);

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
                player.first_name.toLowerCase().includes(search.toLowerCase()) ||
                player.last_name.toLowerCase().includes(search.toLowerCase())
            );
            setSearchResults(filteredResults);
            setShowDropdown(true);
        } else {
            setSearchResults([]);
            setShowDropdown(false);
        }

        console.log(correctPlayer);

    }, [search, allPlayers, guessPlayer]);

    const handleSearchChange = (e) => {
        setSearch(e.target.value);
    };

    const handlePlayerSelect = (player) => {
        setSearch(player.first_name + ' ' + player.last_name);
        setShowDropdown(false);
    };

    const compareGuessPlayer = () => {
        let guessPlayer = allPlayers.find(player => player.first_name + ' ' + player.last_name === search);
        if (guessPlayer.id === correctPlayer.id) {
            setCorrect(true);
            setIncorrectPlayers([...incorrectPlayers, guessPlayer]);
        } else {
            setCorrect(false);
            setIncorrectPlayers([...incorrectPlayers, guessPlayer]);
        }

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
                    <img src={correctPlayer.image_url} alt={`${correctPlayer.first_name} ${correctPlayer.last_name}`} className={`silhouette${correct ? 'correct' : ''}`} />
                    <div className='player-info'>
                        <h2>Who is this player?</h2>
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
                        <button className='button' onClick={compareGuessPlayer}>Guess</button>
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
