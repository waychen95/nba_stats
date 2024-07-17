import requests
import time
import os
import psycopg2
import psycopg2.extras
import pandas as pd
import numpy as np
from dotenv import load_dotenv

class PlayerDatabase():
    def __init__(self, connection, dataframe):
        self.connection = connection
        self.cursor = self.connection.cursor()
        self.dataframe = self._reformat_data(dataframe)

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

        data['number'] = data['number'].astype(int).astype(str)

        data['feet'] = data['feet'].apply(int)
        data['inches'] = data['inches'].apply(int)

        data['team_full_name'] = data['team_url'].apply(lambda x: x.split('/')[-2].strip())
        data['team_id'] = data['team_url'].apply(lambda x: x.split('/')[-3].strip())
        data['position'] = data['position'].apply(lambda x: x.replace('-', '/'))
        
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

        player_df = pd.read_csv('../player_data.csv')
        player_list = player_df.to_dict('records')

        player_db = PlayerDatabase(conn, player_df)

        # player_db.create_player_table()
        # player_db.insert_all_players()
        # player_db.create_team_table()
        # player_db.insert_team()

    

    except Exception as e:
        print(e)
        print(e.with_traceback())

    finally:
        if conn:
            conn.close()

if __name__ == '__main__':
    main()