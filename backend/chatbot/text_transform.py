import pandas as pd

# Load CSVs
players = pd.read_csv('../export/merged_players.csv')
teams = pd.read_csv('../export/teams.csv')
stats = pd.read_csv('../export/merged_stats.csv')

# Merge stats with team names (optional: just for clarity in stats)
# teams_subset = teams[['id', 'name', 'full_name']]
# stats = stats.merge(teams_subset, left_on='team_id', right_on='id', how='left', suffixes=('_stat', '_team'))
# stats = stats.drop(columns=['id'])  # drop team id from merged stats

# Function to combine player info and all stats for that player
def player_text(player_row):
    player_id = player_row['id']

    player_full_name = f"{player_row['first_name']} {player_row['last_name']}"
    
    # Player info
    player_info = ', '.join([f"{col}: {player_row[col]}" for col in player_row.index])
    
    # All stats for that player
    player_stats = stats[stats['player_id'] == player_id]
    if player_stats.empty:
        stats_text = "\nNo Stats Available."
    else:
        stats_text = ""
        for _, stat_row in player_stats.iterrows():
            stats_text += '\n    ' + ', '.join([f"{col}: {stat_row[col]}" for col in stat_row.index])
    
    return f"## {player_full_name}\n### Player Info:\n{player_info}\n### Stats:{stats_text}\n\n"

# Combine all players
all_players_text = ""
all_players_text += "# Players:\n\n"
for _, player_row in players.iterrows():
    all_players_text += player_text(player_row)

# Combine all teams
teams_text = "# Teams:\n\n"
for _, team_row in teams.iterrows():
    teams_text += ', '.join([f"{col}: {team_row[col]}" for col in team_row.index]) + '\n'

# Save to a single text file
with open('embedding_data.txt', 'w', encoding='utf-8') as f:
    f.write(all_players_text)
    f.write('\n' + teams_text)

print("Text file for embedding created: embedding_data.txt")
