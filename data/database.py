import unicodedata
import requests
import time
import os
import psycopg2
import psycopg2.extras
import pandas as pd
import numpy as np
import ast
import math
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

        data = data.dropna(subset=['id', 'number', 'position', 'height', 'weight'])

        # Apply split_height function directly to each element of 'height' column
        heights = data['height'].apply(self.split_height)
        data['feet'], data['inches'] = zip(*heights)

        data.drop('height', axis=1, inplace=True)

        # Clean up 'number' column to remove extra spaces and then convert to integer
        data['number'] = data['number'].astype(str).str.strip()  # Remove extra spaces
        data['number'] = data['number'].apply(lambda x: x.split('-')[0] if '-' in x else x)  # Handle '%s-%s' format
        data['number'] = data['number'].apply(lambda x: x.split(' ')[0] if ' ' in x else x)  # Handle '%s %s' format

        # Convert 'number' to numeric (if possible), handle cases like '7.0' as 7
        def convert_to_int(value):
            try:
                # Try converting value to float first, then to integer if it's a float
                return int(float(value))
            except ValueError:
                print(f"Could not convert {value} to integer")
                return value  # Return the original value if it can't be converted

        # Apply conversion function
        data['number'] = data['number'].apply(convert_to_int).astype(str)  # Convert to integer and back to string

        data['feet'] = data['feet'].apply(int)
        data['inches'] = data['inches'].apply(int)

        # Drop rows with missing team_url
        data = data.dropna(subset=['team_url'])

        data['team_full_name'] = data['team_url'].apply(lambda x: x.split('/')[-2].strip())
        data['team_id'] = data['team_url'].apply(lambda x: x.split('/')[-3].strip())
        data['position'] = data['position'].apply(lambda x: x.replace('-', '/'))

        data['active'] = True

        active_player_df = pd.read_csv('active_players.csv')

        # Set active column to False for players not in active_players.csv
        data.loc[~data['id'].isin(active_player_df['id']), 'active'] = False

        data.to_csv('players/player_data_reformat.csv', index=False)
        
        print(data.head())

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
            country VARCHAR(50),
            active BOOLEAN
        );
        """
        print(create_table)
        self.cursor.execute(create_table)
        self.connection.commit()

    def insert_player(self, player):
        insert_player = """
        INSERT INTO nba_players (id, first_name, last_name, url, image_url, team_id, number, position, feet, inches, weight, last_attended, country, active)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
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
            player['country'],
            player['active']
        ))
        self.connection.commit()

    def insert_all_players(self):
        insert_all_players = """
        INSERT INTO nba_players (id, first_name, last_name, url, image_url, team_id, number, position, feet, inches, weight, last_attended, country, active)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (id) DO NOTHING;
        """

        player_data = []
        players = self.dataframe.to_dict('records')
        print(f'Inserting {len(players)} players')
        
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
                player['country'],
                player['active']
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

    def update_is_active(self):
        update_player = """
        ALTER TABLE nba_players
        ADD COLUMN active BOOLEAN;
        """

        self.cursor.execute(update_player)
        self.connection.commit()

    def update_is_active_players(self):
        update_player = """
        UPDATE nba_players
        SET active = FALSE
        WHERE id = %s;
        """

        player_data = self.dataframe.to_dict('records')
        for player in player_data:
            player_info = (player['id'],)
            self.cursor.execute(update_player, player_info)
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
        self.player_team_df = self._get_player_team_data()

    def _get_player_team_data(self):
        player_stats_df = self.dataframe.copy()

        # missing_data = pd.read_csv('missing_data.csv')

        # missing_ids = missing_data['id'].unique()

        # player_stats_df = player_stats_df[~player_stats_df['player_id'].isin(missing_ids)]

        player_stats_df.drop_duplicates(subset=['player_id', 'team'], inplace=True)

        player_team_df = player_stats_df[['player_id', 'team']].copy()

        player_team_df = player_team_df.groupby('player_id')['team'].apply(list).reset_index()

        player_team_df.columns = ['player_id', 'past_teams']

        player_team_df.to_csv('past_teams/player_team_data.csv', index=False)

        print(player_team_df.head())

        return player_team_df
    

    def _reformat_data(self, dataframe):

        # Convert to DataFrame
        df = dataframe.copy()

        # Drop rows with matching id in the missing data file
        # missing_data = pd.read_csv('missing_data.csv')
        # df = df[~df['player_id'].isin(missing_data['id'])]
        
        team_df = pd.read_csv('team_data.csv')
        df['team_id'] = df['team'].apply(lambda x: team_df[team_df['abbreviation'] == x]['id'].values[0] if len(team_df[team_df['abbreviation'] == x]['id'].values) > 0 else None)

        df.dropna(subset=['team_id'], inplace=True)

        df['team_id'] = df['team_id'].astype('Int64')

        # Sanitize specific columns
        df = df.where(pd.notnull(df), None)

        df.to_csv('player_stats_reformat.csv', index=False)

        return df
    
    def create_player_stats_table(self):
        create_table = """
        CREATE TABLE IF NOT EXISTS nba_player_stats (
            player_id BIGINT REFERENCES nba_players(id),
            year VARCHAR(20),
            team_id BIGINT REFERENCES nba_teams(id),
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
            PRIMARY KEY (player_id, year, team_id)
        );
        """

        self.cursor.execute(create_table)
        self.connection.commit()

    def insert_all_player_stats(self):
        print("Inserting player stats")
        insert_all_player_stats = """
        INSERT INTO nba_player_stats (
            player_id, year, team_id, gp, min, pts, fgm, fga, fg_pct, 
            "3pm", "3pa", "3p_pct",
            ftm, fta, ft_pct, oreb, dreb, reb, 
            ast, tov, stl, blk, pf, fp, dd2, td3, plus_minus
        )
        SELECT
            %s, %s, %s, %s, %s, %s, %s, %s, 
            %s, %s, %s, %s, %s, %s, 
            %s, %s, %s, %s, %s, %s, %s, %s, %s, 
            %s, %s, %s, %s
        WHERE EXISTS (
            SELECT 1 FROM nba_players WHERE id = %s
        ) AND EXISTS (
            SELECT 1 FROM nba_teams WHERE id = %s
        )
        ON CONFLICT (player_id, year, team_id) DO NOTHING;
        """

        data = self.dataframe.copy()
        exception_list = []
        player_stats_data = data.to_dict('records')
        # player_stats_data = self.dataframe.to_dict('records')
        for player_stats in player_stats_data:
            player_stats_info = (
                player_stats['player_id'],
                player_stats['year'],
                player_stats['team_id'],
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
                player_stats['+/-'],
                player_stats['player_id'],
                player_stats['team_id']
            )
            try:
                self.cursor.execute(insert_all_player_stats, player_stats_info)
            except Exception as e:
                print(e)
                exception_list.append(player_stats)
        self.connection.commit()

        print(f"Exceptions: {len(exception_list)}")

        print(f"Inserted {len(player_stats_data)} player stats")

    def update_player_past_team(self):
        update_player = """
        AlTER TABLE nba_players
        ADD COLUMN past_teams TEXT[];
        """

        self.cursor.execute(update_player)
        self.connection.commit()

    def insert_player_past_team(self):
        print("Inserting player past teams")
        player_team_df = self.player_team_df.copy()

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

class PlayerUpdateDatabase():
    def __init__(self, connection, age_number_df, bio_df):
        self.connection = connection
        self.cursor = self.connection.cursor()
        self.age_number_df = self._reformat_age_number_data(age_number_df)
        self.bio_df = self._reformat_bio_data(bio_df)

    def _reformat_bio_data(self, bio_df):
        # Define a function to clean Unicode characters
        def clean_unicode(text):
            if pd.isnull(text):  # Skip null values
                return text
            # Normalize Unicode to NFKD (Decompose characters and remove diacritics)
            normalized = unicodedata.normalize('NFKD', text)
            # Replace specific ambiguous characters (optional)
            cleaned = normalized.translate(str.maketrans({
                '“': '"', '”': '"',  # Replace curly quotes with straight quotes
                '‘': "'", '’': "'",  # Replace curly apostrophes
                '\u00A0': ' ',        # Replace non-breaking space with regular space
                '０': '0', '１': '1', '２': '2', '３': '3', '４': '4',
                '５': '5', '６': '6', '７': '7', '８': '8', '９': '9'  # Full-width to half-width numbers
            }))
            return cleaned
        
        data = bio_df.copy()

        # missing_data = player_df[player_df[['id', 'number', 'position', 'height', 'weight']].isna().any(axis=1)]

        # missing_data.to_csv('missing_bio_data_new.csv', index=False)

        # clean up bio data
        data['professional_bio'] = data['professional_bio'].apply(lambda x: x.replace('\n', ' ') if pd.notnull(x) else None)
        data['personal_bio'] = data['personal_bio'].apply(lambda x: x.replace('\n', ' ') if pd.notnull(x) else None)
        data['before_nba_bio'] = data['before_nba_bio'].apply(lambda x: x.replace('\n', ' ') if pd.notnull(x) else None)

        # clean ambiguous unicode characters
        data['professional_bio'] = data['professional_bio'].apply(clean_unicode)
        data['personal_bio'] = data['personal_bio'].apply(clean_unicode)
        data['before_nba_bio'] = data['before_nba_bio'].apply(clean_unicode)

        data.to_csv('player_bio_reformat.csv', index=False)

        return data

    def _reformat_age_number_data(self, age_number_df):
        data = age_number_df.copy()

        # player_df = pd.read_csv('active_players.csv')
        # missing_data = player_df[player_df[['id', 'number', 'position', 'height', 'weight']].isna().any(axis=1)]

        # missing_data.to_csv('missing_age_data_new.csv', index=False)

        # Set 'number' to None if it is not numeric, except if it is already NULL
        data['number'] = data['number'].apply(lambda x: None if pd.notnull(x) and not str(x).isnumeric() else x)

        # Set 'age' to None if it is not numeric, except if it is already NULL
        data['age'] = data['age'].apply(lambda x: None if pd.notnull(x) and not str(x).isnumeric() else x)

        # set 'birthdate' to '' if it is 'No birthdate available'
        data['birthdate'] = data['birthdate'].apply(lambda x: '' if x == 'No birthdate available' else x)

        # data['number'] = data['number'].apply(lambda x: None if not x.isnumeric() else x)

        data.to_csv('player_number_age_reformat.csv', index=False)

        return data
    
    def update_table(self):
        update_player = """
        ALTER TABLE nba_players
        ADD COLUMN age INT,
        ADD COLUMN bio TEXT;
        """

        self.cursor.execute(update_player)
        self.connection.commit()

    def update_players_age(self):
        print("Updating player ages")
        update_player = """
        UPDATE nba_players
        SET age = %s, birthdate = %s
        WHERE id = %s;
        """

        player_data = self.age_number_df.to_dict('records')
        for player in player_data:
            player_info = (
                player['age'],
                player['birthdate'],
                player['id']
            )
            self.cursor.execute(update_player, player_info)
        self.connection.commit()

    def update_player_bio(self, player_id, bio):
        update_player = """
        UPDATE nba_players
        SET bio = %s
        WHERE id = %s;
        """
        
        self.cursor.execute(update_player, (bio, player_id))
        
        self.connection.commit()

    def update_players_bio(self):
        print("Updating player bios")
        update_player = """
        UPDATE nba_players
        SET professional_bio = %s, personal_bio = %s, before_nba_bio = %s
        WHERE id = %s;
        """

        player_data = self.bio_df.to_dict('records')
        for player in player_data:
            player_info = (
                player['professional_bio'],
                player['personal_bio'],
                player['before_nba_bio'],
                player['id']
            )
            self.cursor.execute(update_player, player_info)
        self.connection.commit()

    def update_null_bio_players(self):
        update_player = """
        UPDATE nba_players
        SET bio = 'No bio available'
        WHERE past_teams is null;
        """

        self.cursor.execute(update_player)
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

        # Š

        # player_df = pd.read_csv('players/player_data_Š.csv')

        # player_db = PlayerDatabase(conn, player_df)

        # player_db.insert_all_players()

    

        # player_stats_df = pd.read_csv('player_stats/player_stats_Š.csv')
        # player_stats_db = PlayerStatsDatabase(conn, player_stats_df)

        # player_stats_db.insert_all_player_stats()

        # player_stats_db.insert_player_past_team()



        player_age_df = pd.read_csv('player_ages/player_number_age_Š.csv')
        player_bio_df = pd.read_csv('player_bios/player_bio_Š.csv')

        print(player_age_df.head())
        print(player_bio_df.head())

        player_update_db = PlayerUpdateDatabase(conn, player_age_df, player_bio_df)

        player_update_db.update_players_age()

        player_update_db.update_players_bio()

        

        
        





    except Exception as e:
        print(e)
        print(e.with_traceback())

    finally:
        if conn:
            conn.close()

if __name__ == '__main__':
    main()