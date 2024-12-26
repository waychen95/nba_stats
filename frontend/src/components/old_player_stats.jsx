import { useState, useEffect } from "react";
import Plot from 'react-plotly.js';
import "../styles/PlayerStats.css";

function PlayerStats({ playerId }) {
    const [stats, setStats] = useState([]);
    const [statsLoading, setStatsLoading] = useState(true);

    useEffect(() => {
        async function fetchStats() {
            try {
                const response = await fetch(`http://localhost:5000/players/${playerId}/stats`);
                const data = await response.json();
        
                // Replace `NaN` values with null or default values
                const sanitizedStats = data.stats.map(stat => {
                    const cleanStat = { ...stat };
                    Object.keys(cleanStat).forEach(key => {
                        if (Number.isNaN(cleanStat[key])) {
                            cleanStat[key] = null; // or set a default value like 0
                        }
                    });
                    return cleanStat;
                });
        
                // Sort the stats by year (ascending order)
                const sortedStats = sanitizedStats.sort((a, b) => b.year - a.year);
        
                setStats(sortedStats);
                setStatsLoading(false);
            } catch (error) {
                console.error("Error fetching stats:", error);
            }
        }        

        fetchStats();
    }, [playerId]);

    // Data preparation for Plotly
    const seasonsTeams = stats.map(stat => `${stat.year} (${stat.team_name})`);
    const minutes = stats.map(stat => stat.min);
    const points = stats.map(stat => stat.pts);
    const rebounds = stats.map(stat => stat.reb);
    const assists = stats.map(stat => stat.ast);
    const steals = stats.map(stat => stat.stl);
    const blocks = stats.map(stat => stat.blk);

    // Aggregate shooting stats for the pie chart
    const totalFGA = stats.reduce((acc, stat) => acc + (stat.fga || 0), 0); // Total field goal attempts
    const total3PA = stats.reduce((acc, stat) => acc + (stat['3pa'] || 0), 0); // Total 3-point attempts
    const totalFTA = stats.reduce((acc, stat) => acc + (stat.fta || 0), 0); // Total free throw attempts

    return (
        <div className="player-stats-container">
            {statsLoading ? (
                <p>Loading...</p>
            ) : (
                <div className="average-stats">
                    <h3>Average Stats</h3>
                    <table>
                        <thead>
                            <tr>
                                <th>Minutes</th>
                                <th>Points</th>
                                <th>Rebounds</th>
                                <th>Assists</th>
                            </tr>
                        </thead>
                        <tbody>
                            <tr>
                                <td>{(minutes.reduce((a, b) => a + b, 0) / minutes.length).toFixed(1)}</td>
                                <td>{(points.reduce((a, b) => a + b, 0) / points.length).toFixed(1)}</td>
                                <td>{(rebounds.reduce((a, b) => a + b, 0) / rebounds.length).toFixed(1)}</td>
                                <td>{(assists.reduce((a, b) => a + b, 0) / assists.length).toFixed(1)}</td>
                            </tr>
                        </tbody>
                    </table>
                </div>
            )}

            <div className="player-stats-advanced">
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
                                        <td>{stat.year ?? 'N/A'}</td>
                                        <td>{stat.team_name ?? 'N/A'}</td>
                                        <td>{stat.gp ?? 'N/A'}</td>
                                        <td>{stat.min ?? 'N/A'}</td>
                                        <td>{stat.pts ?? 'N/A'}</td>
                                        <td>{stat.reb ?? 'N/A'}</td>
                                        <td>{stat.ast ?? 'N/A'}</td>
                                        <td>{stat.stl ?? 'N/A'}</td>
                                        <td>{stat.blk ?? 'N/A'}</td>
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
                                    xaxis: {
                                        title: 'Season (Team)',
                                        tickangle: window.innerWidth < 768 ? -30 : -45, // Adjust angle for smaller screens
                                    },
                                    yaxis: { title: 'Stats' },
                                    margin: {
                                        l: 50, // Left margin
                                        r: 30, // Right margin for mobile
                                        t: 50, // Top margin
                                        b: window.innerWidth < 768 ? 120 : 100, // Bottom margin adjustment
                                    },
                                }}
                                useResizeHandler={true} // Enable responsive resizing
                                style={{ width: '100%', height: window.innerWidth < 768 ? '400px' : '600px' }} // Adjust size dynamically
                                config={{
                                    responsive: true, // Ensure chart adjusts on resize
                                }}
                            />
                        </div>
                    </div>
                )}
                
                {/* Shot Distribution Pie Chart */}
                <div className="player-stats-graph">
                    <Plot
                        data={[
                            {
                                labels: ['2PT', '3PT', 'FT'],
                                values: [totalFGA - total3PA, total3PA, totalFTA], // Aggregated values for pie chart
                                type: 'pie',
                                textinfo: 'label+percent',
                                hoverinfo: 'label+percent',
                                marker: { colors: ['blue', 'red', 'yellow'] },
                            },
                        ]}
                        layout={{
                            title: 'Shot Distribution (2PT, 3PT, FT)',
                        }}
                    />
                </div>
            </div>
        </div>
    );
}

export default PlayerStats;
