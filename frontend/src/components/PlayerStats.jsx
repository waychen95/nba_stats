import { useState, useEffect } from "react";
import Plot from 'react-plotly.js';
import "../styles/PlayerStats.css";

function PlayerStats({ playerId }) {
    const [stats, setStats] = useState([]);
    const [statsLoading, setStatsLoading] = useState(true);

    useEffect(() => {
        async function fetchStats() {
            const response = await fetch(`http://localhost:5000/players/${playerId}/stats`);
            const data = await response.json();
            
            // Sort the stats by year (ascending order)
            const sortedStats = data.stats.sort((a, b) => b.year - a.year);
            
            setStats(sortedStats);
            setStatsLoading(false);
        }

        fetchStats();
    }, [playerId]);

    // Data preparation for Plotly
    const seasonsTeams = stats.map(stat => `${stat.year} (${stat.team_name})`);
    const minutes = stats.map(stat => stat.min);
    const points = stats.map(stat => stat.pts);
    const rebounds = stats.map(stat => stat.reb);
    const assists = stats.map(stat => stat.ast);

    return (
        <div className="player-stats-container">
            {statsLoading ? (
                <p>Loading...</p>
            ) : (
                <div className="stats">
                    <h3>Stats</h3>
                    <table>
                        <thead>
                            <tr>
                                <th>Season</th>
                                <th>Team</th>
                                <th>Games</th>
                                <th>Minutes</th>
                                <th>Points</th>
                                <th>Rebounds</th>
                                <th>Assists</th>
                                <th>Steals</th>
                                <th>Blocks</th>
                            </tr>
                        </thead>
                        <tbody className="player-stats-list">
                            {stats.map((stat) => (
                                <tr key={stat.year + stat.team_name} className="player-stats">
                                    <td>{stat.year}</td>
                                    <td>{stat.team_name}</td>
                                    <td>{stat.gp}</td>
                                    <td>{stat.min}</td>
                                    <td>{stat.pts}</td>
                                    <td>{stat.reb}</td>
                                    <td>{stat.ast}</td>
                                    <td>{stat.stl}</td>
                                    <td>{stat.blk}</td>
                                </tr>
                            ))}
                        </tbody>
                    </table>

                    <div className="player-stats-graph">
                        <Plot
                            data={[
                                {
                                    x: seasonsTeams,
                                    y: minutes,
                                    type: 'scatter',
                                    mode: 'lines+markers',
                                    marker: { color: 'black' },
                                    name: 'Minutes',
                                },
                                {
                                    x: seasonsTeams,
                                    y: points,
                                    type: 'scatter',
                                    mode: 'lines+markers',
                                    marker: { color: 'red' },
                                    name: 'Points',
                                },
                                {
                                    x: seasonsTeams,
                                    y: rebounds,
                                    type: 'scatter',
                                    mode: 'lines+markers',
                                    marker: { color: 'blue' },
                                    name: 'Rebounds',
                                },
                                {
                                    x: seasonsTeams,
                                    y: assists,
                                    type: 'scatter',
                                    mode: 'lines+markers',
                                    marker: { color: 'green' },
                                    name: 'Assists',
                                }
                            ]}
                            layout={{ 
                                title: `Player Stats Across Seasons and Teams`, 
                                xaxis: { title: 'Season (Team)' }, 
                                yaxis: { title: 'Stats' } 
                            }}
                        />
                    </div>
                </div>
            )}
        </div>
    );
}

export default PlayerStats;
