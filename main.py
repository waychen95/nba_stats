import pandas as pd
import numpy as np
import requests
import time

year = '2023-24'

player_url = f'https://stats.nba.com/stats/leagueLeaders?LeagueID=00&PerMode=PerGame&Scope=S&Season={year}&SeasonType=Playoffs&StatCategory=PTS'

players = requests.get(player_url).json()

player_data = pd.DataFrame(players['resultSet']['rowSet'], columns=players['resultSet']['headers'])

csv_file = f'player_data{year}.csv'

player_data.to_csv(csv_file, index=False)

print(player_url)
print(player_data.head())