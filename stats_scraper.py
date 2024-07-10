import pandas as pd
import numpy as np
import requests
import time

start_year = 2020
end_year = 2021
years = []

for year in range(start_year, end_year):
    year_end = year + 1
    year_end = str(year_end)[-2:]
    years.append(f'{year}-{year_end}')

type = 'Regular Season'

for year in years:
    player_url = f'https://stats.nba.com/stats/leagueLeaders?LeagueID=00&PerMode=PerGame&Scope=S&Season={year}&SeasonType={type}&StatCategory=PTS'

    print(player_url)

    players = requests.get(player_url).json()

    player_data = pd.DataFrame(players['resultSet']['rowSet'], columns=players['resultSet']['headers'])

    player_data['SEASON'] = year

    player_data.drop(columns=['RANK'], inplace=True)

    print(player_data.head())

    # csv_file = f'player_data_{year}.csv'

    # player_data.to_csv(csv_file, index=False)

    # print(player_data.head())

    random_sleep = np.random.randint(5, 10)

    time.sleep(random_sleep)
