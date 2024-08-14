import requests
import time
import os
import psycopg2
import psycopg2.extras
import pandas as pd
import numpy as np
import ast
from dotenv import load_dotenv

class PlayerDatabase():
    def __init__(self, connection, dataframe):
        self.connection = connection
        self.cursor = self.connection.cursor()
        self.dataframe = self._reformat_data(dataframe)

    def get_player_db(self):
        return self.dataframe

    def split_height( self, height):
        split_height = height.split('-')
        feet = int(split_height[0])
        inches = int(split_height[1])
        return feet, inches

    def _reformat_data(self, dataframe):
        data = dataframe.copy()
        print(f"Dropping {len(data) - len(data.dropna(subset=['id', 'number', 'position', 'height', 'weight']))} rows with missing values")

        missing_data = data[data[['id', 'number', 'position', 'height', 'weight']].isna().any(axis=1)]

        data = data.dropna(subset=['id', 'number', 'position', 'height', 'weight'])

        # Apply split_height function directly to each element of 'height' column
        heights = data['height'].apply(self.split_height)
        data['feet'], data['inches'] = zip(*heights)

        data.drop('height', axis=1, inplace=True)

        data['number'] = data['number'].astype(int).astype(str)

        data['feet'] = data['feet'].apply(int)
        data['inches'] = data['inches'].apply(int)

        data['team_full_name'] = data['team_url'].apply(lambda x: x.split('/')[-2].strip())
        data['team_id'] = data['team_url'].apply(lambda x: x.split('/')[-3].strip())
        data['position'] = data['position'].apply(lambda x: x.replace('-', '/'))
        
        print(data.head())

        missing_data.to_csv('missing_data.csv', index=False)

        return data
    
    def create_team_table(self):
        create_table = """
        CREATE TABLE IF NOT EXISTS nba_teams (
            id BIGINT PRIMARY KEY,
            name VARCHAR(50),
            full_name VARCHAR(50),
            url VARCHAR(255)
        );
        """
        print(create_table)
        self.cursor.execute(create_table)
        self.connection.commit()

    def insert_team(self):
        insert_team = """
        INSERT INTO nba_teams (id, name, full_name, url)
        VALUES (%s, %s, %s, %s)
        """
        unique_team = self.dataframe[['team_id', 'team', 'team_full_name', 'team_url']].drop_duplicates()
        team_data = unique_team.to_dict('records')
        for team in team_data:
            self.cursor.execute(insert_team, (team['team_id'], team['team'], team['team_full_name'], team['team_url']))
        print(insert_team)
        self.connection.commit()

    def create_player_table(self):
        create_table = """
        CREATE TABLE IF NOT EXISTS nba_players (
            id BIGINT PRIMARY KEY,
            first_name VARCHAR(50),
            last_name VARCHAR(50),
            url VARCHAR(255),
            image_url VARCHAR(255),
            team_id BIGINT REFERENCES nba_teams(id),
            number VARCHAR(50),
            position VARCHAR(50),
            feet INT,
            inches INT,
            weight VARCHAR(50),
            last_attended VARCHAR(50),
            country VARCHAR(50)
        );
        """
        print(create_table)
        self.cursor.execute(create_table)
        self.connection.commit()

    def insert_player(self, player):
        insert_player = """
        INSERT INTO nba_players (id, first_name, last_name, url, image_url, team_id, number, position, feet, inches, weight, last_attended, country)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        print(insert_player)
        self.cursor.execute(insert_player, (
            int(player['id']),
            player['first_name'],
            player['last_name'],
            player['url'],
            player['image_url'],
            player['team_id'],
            player['number'],
            player['position'],
            player['feet'],
            player['inches'],
            player['weight'],
            player['last_attended'],
            player['country']
        ))
        self.connection.commit()

    def insert_all_players(self):
        insert_all_players = """
        INSERT INTO nba_players (id, first_name, last_name, url, image_url, team_id, number, position, feet, inches, weight, last_attended, country)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """

        player_data = []
        players = self.dataframe.to_dict('records')
        
        for player in players:
            if player is None:
                print('Player is None')
                continue
            player_info = (
                int(player['id']),
                player['first_name'],
                player['last_name'],
                player['url'],
                player['image_url'],
                player['team_id'],
                player['number'],
                player['position'],
                player['feet'],
                player['inches'],
                player['weight'],
                player['last_attended'],
                player['country']
            )
            player_data.append(player_info)

        
        self.cursor.executemany(insert_all_players, player_data)
        self.connection.commit()

    def get_players(self):
        query = """
        SELECT * FROM nba_players;
        """
        print(query)
        self.cursor.execute(query)
        return self.cursor.fetchall()
    
    def get_player(self, player_id):
        query = """
        SELECT * FROM nba_players WHERE id = %s;
        """
        print(query)
        self.cursor.execute(query, (player_id,))
        return self.cursor.fetchone()
    
    def update_player(self, player_updates, player_id):
        update_player = """
        UPDATE nba_players
        SET first_name = %s, last_name = %s, url = %s, image_url = %s, team_id = %s, number = %s, position = %s, feet = %s, inches = %s, weight = %s, last_attended = %s, country = %s
        WHERE id = %s;
        """
        self.cursor.execute(update_player, player_updates, player_id)
        self.connection.commit()

    def delete_player(self, player_id):
        delete_player = """
        DELETE FROM nba_players WHERE id = %s;
        """
        self.cursor.execute(delete_player, (player_id,))
        self.connection.commit()

    def __del__(self):
        self.cursor.close()

class TeamDatabase():
    def __init__(self, connection, dataframe):
        self.connection = connection
        self.cursor = self.connection.cursor()
        self.dataframe = self._reformat_data(dataframe)

    # Define a function to get the conference based on team name or other criteria
    def _get_conference(self, team_id):
        # Update this function based on how you want to determine the conference
        eastern_teams = [
            1610612738,  # Boston Celtics
            1610612751,  # Brooklyn Nets
            1610612752,  # New York Knicks
            1610612755,  # Philadelphia 76ers
            1610612761,  # Toronto Raptors
            1610612741,  # Chicago Bulls
            1610612739,  # Cleveland Cavaliers
            1610612749,  # Milwaukee Bucks
            1610612754,  # Indiana Pacers
            1610612737,  # Atlanta Hawks
            1610612766,  # Charlotte Hornets
            1610612748,  # Miami Heat
            1610612753,  # Orlando Magic
            1610612764,  # Washington Wizards
            1610612740,  # New Orleans Pelicans (Moved to Western Conference)
        ]
        if team_id in eastern_teams:
            return 'Eastern'
        else:
            return 'Western'
        
    def _get_logo_url(self, team_id):
        image_base_url = 'https://cdn.nba.com/logos/nba/'
        team_id = str(team_id)

        return f"{image_base_url}{team_id}/global/L/logo.svg"

    def _reformat_data(self, dataframe):
        data = dataframe.copy()
        # data['conference'] = data['id'].apply(self._get_conference)

        # data.drop(columns=['logo_url'], inplace=True)

        # data['logo_url'] = data['id'].apply(self._get_logo_url)

        # Convert string representations of lists to actual lists
        data['associate_head_coach'] = data['associate_head_coach'].apply(lambda x: ast.literal_eval(x) if pd.notnull(x) else [])
        data['assistant_coach'] = data['assistant_coach'].apply(lambda x: ast.literal_eval(x) if pd.notnull(x) else [])

        print(data.head())

        return data

    def alter_team_table(self):
        alter_table = """
        ALTER TABLE nba_teams
        ADD COLUMN city VARCHAR(50),
        ADD COLUMN logo_url VARCHAR(255),
        ADD COLUMN conference VARCHAR(50),
        ADD COLUMN head_coach VARCHAR(50),
        ADD COLUMN associate_coach TEXT[],
        ADD COLUMN assistant_coach TEXT[];
        """
        self.cursor.execute(alter_table)
        self.connection.commit()

    def update_team(self, team_updates, team_id):
        update_team = """
        UPDATE nba_teams
        SET city = %s, logo_url = %s, conference = %s, head_coach = %s, associate_coach = %s, assistant_coach = %s
        WHERE id = %s;
        """
        self.cursor.execute(update_team, team_updates, team_id)
        self.connection.commit()

    def update_all_teams(self):
        update_team = """
        UPDATE nba_teams
        SET city = %s, logo_url = %s, conference = %s, head_coach = %s, associate_coach = %s, assistant_coach = %s
        WHERE id = %s;
        """
        team_data = self.dataframe.to_dict('records')
        for team in team_data:
            team_info = (
                team['city'],
                team['logo_url'],
                team['conference'],
                team['head_coach'],
                team['associate_head_coach'],
                team['assistant_coach'],
                team['id']
            )
            self.cursor.execute(update_team, team_info)
        self.connection.commit()

    def update_conferences(self):
        update_conference = """
        UPDATE nba_teams
        SET conference = %s
        WHERE id = %s;
        """
        
        team_data = self.dataframe.to_dict('records')
        for team in team_data:
            team_info = (
                team['conference'],
                team['id']
            )
            self.cursor.execute(update_conference, team_info)
        self.connection.commit()

    def update_logo_urls(self):
        update_logo_url = """
        UPDATE nba_teams
        SET logo_url = %s
        WHERE id = %s;
        """
        team_data = self.dataframe.to_dict('records')
        for team in team_data:
            team_info = (
                team['logo_url'],
                team['id']
            )
            self.cursor.execute(update_logo_url, team_info)
        self.connection.commit()

    def update_assistant_coaches(self):
        update_assistant_coaches = """
        UPDATE nba_teams
        SET assistant_coach = %s
        WHERE id = %s;
        """
        team_data = self.dataframe.to_dict('records')
        for team in team_data:
            team_info = (
                team['assistant_coach'],
                team['id']
            )
            self.cursor.execute(update_assistant_coaches, team_info)
        self.connection.commit()

    def update_associate_coaches(self):
        update_associate_coaches = """
        UPDATE nba_teams
        SET associate_coach = %s
        WHERE id = %s;
        """
        team_data = self.dataframe.to_dict('records')
        for team in team_data:
            team_info = (
                team['associate_head_coach'],
                team['id']
            )
            print(team['associate_head_coach'])
            self.cursor.execute(update_associate_coaches, team_info)
        self.connection.commit()

class PlayerStatsDatabase():
    def __init__(self, connection, dataframe):
        self.connection = connection
        self.cursor = self.connection.cursor()
        self.dataframe = self._reformat_data(dataframe)

    def _get_player_team_data(self):
        player_stats_df = pd.read_csv('player_stats_all_new.csv')

        missing_data = pd.read_csv('missing_data_old.csv')

        missing_ids = missing_data['id'].unique()

        player_stats_df = player_stats_df[~player_stats_df['player_id'].isin(missing_ids)]

        player_stats_df.drop_duplicates(subset=['player_id', 'team'], inplace=True)

        player_team_df = player_stats_df[['player_id', 'team']].copy()

        player_team_df = player_team_df.groupby('player_id')['team'].apply(list).reset_index()

        player_team_df.columns = ['player_id', 'past_teams']

        print(player_team_df.head())

        return player_team_df

    def _clean_and_convert(self, value):
        # Split the value by dot and take the first segment
        cleaned_value_list = value.split('.')
        if len(cleaned_value_list) > 2:
            cleaned_value = cleaned_value_list[0] + '.' + cleaned_value_list[1]
        else:
            cleaned_value = value
        try:
            return float(cleaned_value)
        except ValueError:
            return None  # Handle as appropriate

    def _reformat_data(self, dataframe):

        # Convert to DataFrame
        df = dataframe.copy()

        # Drop rows with matching id in the missing data file
        missing_data = pd.read_csv('missing_data_old.csv')
        df = df[~df['player_id'].isin(missing_data['id'])]

        # Group by player_id and year, and sum or average the stats
        agg_df = df.groupby(['player_id', 'year']).agg({
            'gp': 'sum',
            'min': 'mean',
            'pts': 'mean',
            'fgm': 'sum',
            'fga': 'sum',
            'fg%': 'mean',
            '3pm': 'sum',
            '3pa': 'sum',
            '3p%': 'mean',
            'ftm': 'sum',
            'fta': 'sum',
            'ft%': 'mean',
            'oreb': 'sum',
            'dreb': 'sum',
            'reb': 'sum',
            'ast': 'sum',
            'tov': 'sum',
            'stl': 'sum',
            'blk': 'sum',
            'pf': 'sum',
            'fp': 'mean',
            'dd2': 'sum',
            'td3': 'sum',
            '+/-': 'mean'
        }).reset_index()

        agg_df = agg_df.round(3)

        agg_df['fta'] = agg_df['fta'].apply(lambda x: self._clean_and_convert(x))

        print(agg_df.head())

        return agg_df
    
    def create_player_stats_table(self):
        create_table = """
        CREATE TABLE IF NOT EXISTS nba_player_stats (
            player_id BIGINT REFERENCES nba_players(id),
            year VARCHAR(20),
            gp INT,
            min FLOAT,
            pts FLOAT,
            fgm FLOAT,
            fga FLOAT,
            fg_pct FLOAT,
            "3pm" FLOAT,
            "3pa" FLOAT,
            "3p_pct" FLOAT,
            ftm FLOAT,
            fta FLOAT,
            ft_pct FLOAT,
            oreb FLOAT,
            dreb FLOAT,
            reb FLOAT,
            ast FLOAT,
            tov FLOAT,
            stl FLOAT,
            blk FLOAT,
            pf FLOAT,
            fp FLOAT,
            dd2 INT,
            td3 INT,
            plus_minus FLOAT,
            PRIMARY KEY (player_id, year)
        );
        """

        self.cursor.execute(create_table)
        self.connection.commit()

    def insert_player_stats(self, player_stats):
        insert_player_stats = """
        INSERT INTO nba_player_stats (player_id, year, gp, min, pts, fgm, fga, fg_pct, 3pm, 3pa, 3p_pct, ftm, fta, ft_pct, oreb, dreb, reb, ast, tov, stl, blk, pf, fp, dd2, td3, plus_minus)
        VALUES (%
        """
        self.cursor.execute(insert_player_stats, player_stats)
        self.connection.commit()

    def insert_all_player_stats(self):
        insert_all_player_stats = """
        INSERT INTO nba_player_stats (
            player_id, year, gp, min, pts, fgm, fga, fg_pct, 
            "3pm", "3pa", "3p_pct",  -- Enclose these columns in double quotes
            ftm, fta, ft_pct, oreb, dreb, reb, 
            ast, tov, stl, blk, pf, fp, dd2, td3, plus_minus
        )
        VALUES (
            %s, %s, %s, %s, %s, %s, %s, %s, 
            %s, %s, %s, %s, %s, %s, 
            %s, %s, %s, %s, %s, %s, %s, %s, %s, 
            %s, %s, %s
        );
        """

        player_stats_data = self.dataframe.to_dict('records')
        for player_stats in player_stats_data:
            player_stats_info = (
                player_stats['player_id'],
                player_stats['year'],
                player_stats['gp'],
                player_stats['min'],
                player_stats['pts'],
                player_stats['fgm'],
                player_stats['fga'],
                player_stats['fg%'],
                player_stats['3pm'],
                player_stats['3pa'],
                player_stats['3p%'],
                player_stats['ftm'],
                player_stats['fta'],
                player_stats['ft%'],
                player_stats['oreb'],
                player_stats['dreb'],
                player_stats['reb'],
                player_stats['ast'],
                player_stats['tov'],
                player_stats['stl'],
                player_stats['blk'],
                player_stats['pf'],
                player_stats['fp'],
                player_stats['dd2'],
                player_stats['td3'],
                player_stats['+/-']
            )
            self.cursor.execute(insert_all_player_stats, player_stats_info)
        self.connection.commit()

    def update_player_past_team(self):
        update_player = """
        AlTER TABLE nba_players
        ADD COLUMN past_teams TEXT[];
        """

        self.cursor.execute(update_player)
        self.connection.commit()

    def insert_player_past_team(self):
        player_team_df = self._get_player_team_data()

        update_team = """
        UPDATE nba_players
        SET past_teams = %s
        WHERE id = %s;
        """

        player_team_data = player_team_df.to_dict('records')
        for player_team in player_team_data:
            player_team_info = (
                player_team['past_teams'],
                player_team['player_id']
            )
            self.cursor.execute(update_team, player_team_info)
        self.connection.commit()



def main():
    # Load environment variables
    load_dotenv()

    hostname = os.getenv('HOSTNAME')
    username = os.getenv('USER')
    password = os.getenv('PASSWORD')
    database = os.getenv('DATABASE')
    port = os.getenv('PORT')

    conn = None

    try:
        conn = psycopg2.connect(
            host=hostname,
            user=username,
            password=password,
            dbname=database,
            port=port
        )

        if conn:
            print('Connected to database')

        
        # player_df = pd.read_csv('player_data_old.csv')

        # new_player_df = pd.read_csv('player_data_new.csv')

        # player_db.insert_all_players()

        # player_db.create_player_table()
        # player_db.insert_all_players()
        # player_db.create_team_table()
        # player_db.insert_team()

        # team_df = pd.read_csv('team_data.csv')
        # team_db = TeamDatabase(conn, team_df)

        # team_db.update_logo_urls()

        # team_db.alter_team_table()
        # team_db.update_all_teams()

        player_stats_df = pd.read_csv('player_stats_all_new.csv')
        player_stats_db = PlayerStatsDatabase(conn, player_stats_df)

        # player_stats_db.insert_player_past_team()

        # player_stats_db.create_player_stats_table()
        # player_stats_db.insert_all_player_stats()





    except Exception as e:
        print(e)
        print(e.with_traceback())

    finally:
        if conn:
            conn.close()

if __name__ == '__main__':
    main()