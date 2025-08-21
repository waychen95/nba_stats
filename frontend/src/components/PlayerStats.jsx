import { useState, useEffect } from "react";
import Plot from 'react-plotly.js';
import Loading from '../components/Loading';
import "../styles/PlayerStats.css";


function PlayerStats({ playerId, teamName }) {
    const [stats, setStats] = useState([]);
    const [statsLoading, setStatsLoading] = useState(true);
    const [statBoardColor, setStatBoardColor] = useState("");
    const [selectedGraph, setSelectedGraph] = useState("shotDistribution");

    const statBoardColors = [
        { team: "hawks", color: "#660000" },
        { team: "celtics", color: "#004D26" },
        { team: "nets", color: "#2B2B2B" },
        { team: "hornets", color: "#140066" },
        { team: "bulls", color: "#660000" },
        { team: "cavaliers", color: "#4D0020" },
        { team: "mavericks", color: "#002044" },
        { team: "nuggets", color: "#002244" },
        { team: "pistons", color: "#80001F" },
        { team: "warriors", color: "#0C2444" },
        { team: "rockets", color: "#660000" },
        { team: "pacers", color: "#002244" },
        { team: "clippers", color: "#660033" },
        { team: "lakers", color: "#33005C" },
        { team: "grizzlies", color: "#3D4873" },
        { team: "heat", color: "#660019" },
        { team: "bucks", color: "#00401A" },
        { team: "timberwolves", color: "#0C2444" },
        { team: "pelicans", color: "#002244" },
        { team: "knicks", color: "#003C73" },
        { team: "thunder", color: "#004266" },
        { team: "magic", color: "#004D80" },
        { team: "sixers", color: "#003C73" },
        { team: "suns", color: "#14004D" },
        { team: "blazers", color: "#660000" },
        { team: "kings", color: "#33005C" },
        { team: "spurs", color: "#2B2B2B" },
        { team: "raptors", color: "#660000" },
        { team: "jazz", color: "#002244" },
        { team: "wizards", color: "#66001A" }
    ];    

    useEffect(() => {
        async function fetchStats() {
            try {
                const response = await fetch(`https://d1zi95jowxdkwf.cloudfront.net/players/${playerId}/stats`);
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

                const statBoardColor = statBoardColors.find(statBoardColor => statBoardColor.team === teamName.toLowerCase())?.color;

                setStatBoardColor(statBoardColor);
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

    const renderGraph = () => {
        switch (selectedGraph) {
            case "shotDistribution":
                return (
                    <Plot
                        data={[
                            {
                                labels: ['2PT', '3PT', 'FT'],
                                values: [totalFGA - total3PA, total3PA, totalFTA],
                                type: 'pie',
                                textinfo: 'label+percent',
                                hoverinfo: 'label+percent',
                                marker: {
                                    colors: ['#1E88E5', '#6A1B9A', '#FFB300'], // Cool tones for modern UI
                                },
                            },
                        ]}
                        layout={{
                            title: {
                                text: 'Shot Distribution (2PT, 3PT, FT)',
                                font: {
                                    family: 'Arial, sans-serif',
                                    size: 18,
                                    color: '#333',
                                },
                            },
                            showlegend: true, // Enable legend for better UX
                            legend: {
                                x: 0.5, // Center the legend horizontally
                                y: -0.5, // Place it below the chart
                                xanchor: 'center', // Align to center horizontally
                                font: {
                                    size: 12,
                                    color: '#333',
                                },
                            },
                            height: 450,
                            width: 450,
                            paper_bgcolor: '#F9F9F9', // Light grey background for modern aesthetics
                            plot_bgcolor: '#F9F9F9',
                        }}
                    />
                );
            case "minutesPerGame":
                return (
                    <Plot
                        data={[
                            {
                                x: seasonsTeams,
                                y: minutes,
                                type: 'bar',
                                marker: { color: 'green' },
                            },
                        ]}
                        layout={{
                            title: 'Minutes Per Game Over Seasons',
                            xaxis: { title: 'Season (Team)',
                                tickfont: {
                                    size: 10, // Adjust font size for better readability
                                },
                                tickangle: 35, // Rotate x-axis labels for better readability
                             },
                            yaxis: { title: 'Minutes' },
                            height: 400,
                            width: 500,
                        }}
                    />
                );
            case "pointsOverTime":
                return (
                    <Plot
                        data={[
                            {
                                x: seasonsTeams,
                                y: points,
                                type: 'scatter',
                                mode: 'lines+markers',
                                marker: { color: 'blue' },
                            },
                        ]}
                        layout={{
                            title: 'Points Over Seasons',
                            xaxis: { title: 'Season (Team)',
                                tickfont: {
                                    size: 10, // Adjust font size for better readability
                                },
                                tickangle: 35, // Rotate x-axis labels for better readability
                             },
                            yaxis: { title: 'Points' },
                            height: 400,
                            width: 500,
                        }}
                    />
                );
            case "reboundsOverTime":
                return (
                    <Plot
                        data={[
                            {
                                x: seasonsTeams,
                                y: rebounds,
                                type: 'scatter',
                                mode: 'lines+markers',
                                marker: { color: 'green' },
                            },
                        ]}
                        layout={{
                            title: 'Rebounds Over Seasons',
                            xaxis: { title: 'Season (Team)',
                                tickfont: {
                                    size: 10, // Adjust font size for better readability
                                },
                                tickangle: 35, // Rotate x-axis labels for better readability
                             },
                            yaxis: { title: 'Rebounds' },
                            height: 400,
                            width: 500,
                        }}
                    />
                );
            case "assistsOverTime":
                return (
                    <Plot
                        data={[
                            {
                                x: seasonsTeams,
                                y: assists,
                                type: 'scatter',
                                mode: 'lines+markers',
                                marker: { color: 'red' },
                            },
                        ]}
                        layout={{
                            title: 'Assists Over Seasons',
                            xaxis: { title: 'Season (Team)',
                                tickfont: {
                                    size: 10, // Adjust font size for better readability
                                },
                                tickangle: 35, // Rotate x-axis labels for better readability
                             },
                            yaxis: { title: 'Assists' },
                            height: 400,
                            width: 500,
                        }}
                    />
                );
            case "stealsOverTime":
                return (
                    <Plot
                        data={[
                            {
                                x: seasonsTeams,
                                y: steals,
                                type: 'scatter',
                                mode: 'lines+markers',
                                marker: { color: 'purple' },
                            },
                        ]}
                        layout={{
                            title: 'Steals Over Seasons',
                            xaxis: { title: 'Season (Team)',
                                tickfont: {
                                    size: 10, // Adjust font size for better readability
                                },
                                tickangle: 35, // Rotate x-axis labels for better readability
                             },
                            yaxis: { title: 'Steals' },
                            height: 400,
                            width: 500,
                        }}
                    />
                );
            case "blocksOverTime":
                return (
                    <Plot
                        data={[
                            {
                                x: seasonsTeams,
                                y: blocks,
                                type: 'scatter',
                                mode: 'lines+markers',
                                marker: { color: 'orange' },
                            },
                        ]}
                        layout={{
                            title: 'Blocks Over Seasons',
                            xaxis: { title: 'Season (Team)',
                                tickfont: {
                                    size: 10, // Adjust font size for better readability
                                },
                                tickangle: 35, // Rotate x-axis labels for better readability
                             },
                            yaxis: { title: 'Blocks' },
                            height: 400,
                            width: 500,
                        }}
                    />
                );
            default:
                return null;
        }
    };

    return (
        <div className="player-stats-container">
            {statsLoading ? (
                <Loading />
            ) : (
                <div className="player-stats-summary">
                    <h2>Career Stats (Regular Season)</h2>
                    <div className="average-stats" style={{ background: statBoardColor }}>
                        <div className="points">
                            <div className="stat-title">Points</div>
                            <div className="stat-value">
                                {(points.reduce((a, b) => a + b, 0) / points.length).toFixed(1)}
                            </div>
                        </div>
                        <div className="other-stats">
                            <div className="stat-item">
                                <div className="stat-title">Rebounds</div>
                                <div className="stat-value">
                                    {(rebounds.reduce((a, b) => a + b, 0) / rebounds.length).toFixed(1)}
                                </div>
                            </div>
                            <div className="stat-item">
                                <div className="stat-title">Assists</div>
                                <div className="stat-value">
                                    {(assists.reduce((a, b) => a + b, 0) / assists.length).toFixed(1)}
                                </div>
                            </div>
                            <div className="stat-item">
                                <div className="stat-title">Steals</div>
                                <div className="stat-value">
                                    {(steals.reduce((a, b) => a + b, 0) / steals.length).toFixed(1)}
                                </div>
                            </div>
                            <div className="stat-item">
                                <div className="stat-title">Blocks</div>
                                <div className="stat-value">
                                    {(blocks.reduce((a, b) => a + b, 0) / blocks.length).toFixed(1)}
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            )}

            <div className="player-stats-advanced-container">
                <h2>Player Stats</h2>
                <div className="player-stats-advanced">
                    <div className="graph-selector">
                        <label htmlFor="graphType">Select Graph:</label>
                        <select
                            id="graphType"
                            value={selectedGraph}
                            onChange={(e) => setSelectedGraph(e.target.value)}
                        >
                            <option value="shotDistribution">Shot Distribution</option>
                            <option value="minutesPerGame">Minutes Per Game</option>
                            <option value="pointsOverTime">Points Over Time</option>
                            <option value="reboundsOverTime">Rebounds Over Time</option>
                            <option value="assistsOverTime">Assists Over Time</option>
                            <option value="stealsOverTime">Steals Over Time</option>
                            <option value="blocksOverTime">Blocks Over Time</option>
                        </select>
                    </div>

                    <div className="player-stats-graph">
                        {renderGraph()}
                    </div>
                </div>
            </div>
        </div>
    );
}

export default PlayerStats;
