import pandas as pd
import numpy as np
import requests
import time
import os
# import psycopg2
from dotenv import load_dotenv
from sqlalchemy import create_engine
import pandas as pd
import numpy as np

class PlayerDatabase():
    def __init__(self, connection):
        self.connection = connection
        self.cursor = self.connection.cursor()

    def create_player_table(self):
        create_table = """
        CREATE TABLE IF NOT EXISTS players (
            id INT PRIMARY KEY,
            first_name VARCHAR(50),
            last_name VARCHAR(50),
            url VARCHAR(255),
            image_url VARCHAR(255),
            team VARCHAR(50),
            team_url VARCHAR(255),
            number INT,
            position VARCHAR(50),
            height VARCHAR(50),
            weight INT,
            last_attended VARCHAR(50),
            country VARCHAR(50)
        );
        """
        self.cursor.execute(create_table)
        self.connection.commit()

    def insert_player(self, player):
        insert_player = """
        INSERT INTO players (id, first_name, last_name, url, image_url, team, team_url, number, position, height, weight, last_attended, country)
        VALUES (% 
        """
        self.cursor.execute(insert_player, player)
        self.connection.commit()

    def get_players(self):
        query = """
        SELECT * FROM players;
        """
        self.cursor.execute(query)
        return self.cursor.fetchall()
    
def write_to_database(player_df, table_name, db_url):
    engine = create_engine(db_url)
    player_df.to_sql(table_name, engine, if_exists='replace', index=False)

def main():
    # Load environment variables
    load_dotenv()

    hostname = os.getenv('HOSTNAME')
    username = os.getenv('USER')
    password = os.getenv('PASSWORD')
    database = os.getenv('DATABASE')
    port = os.getenv('PORT')

    print(hostname, username, password, database, port)

    try:

        global db_url

        db_config = {
            'user': username,
            'password': password,
            'host': hostname,
            'port': port,
            'database': database
        }

        db_url = f"postgresql://{db_config['user']}:{db_config['password']}@{db_config['host']}:{db_config['port']}/{db_config['database']}"

        player_df = pd.read_csv('player_data.csv')

        write_to_database(player_df, database, db_url)
    
    except Exception as e:
        print(e)

    # conn = None
    # cur = None

    # try:
    #     conn = psycopg2.connect(
    #         host=hostname,
    #         user=username,
    #         password=password,
    #         dbname=database,
    #         port=port
    #     )

    #     cur = conn.cursor()

    #     print('Connected to database')

    #     player_df = pd.read_csv('player_data.csv')

    #     player_db = PlayerDatabase(conn)
    #     player_db.create_player_table()



    # except Exception as e:
    #     print(e)

    # finally:
    #     if conn:
    #         conn.close()
    #     if cur:
    #         cur.close()

if __name__ == '__main__':
    main()