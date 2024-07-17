import os
import psycopg2
import psycopg2.extras
import pandas as pd
import numpy as np
from dotenv import load_dotenv

class guessGame():

    def __init__(self):
        # Load environment variables
        load_dotenv()

        hostname = os.getenv('HOSTNAME')
        username = os.getenv('USER')
        password = os.getenv('PASSWORD')
        database = os.getenv('DATABASE')
        port = os.getenv('PORT')

        # Connect to the PostgreSQL database
        try:
            connection = psycopg2.connect(
                host=hostname,
                user=username,
                password=password,
                dbname=database,
                port=port
            )
            print("Connected to the database")

            self.connection = connection
            self.cursor = self.connection.cursor(cursor_factory=psycopg2.extras.DictCursor)
            self.players = self._get_all_players()
        except Exception as e:
            print(f"Error: {e.with_traceback()}")
    
    def _get_all_players(self):
        self.cursor.execute("SELECT * FROM nba_players")
        print("Getting all players")
        return self.cursor.fetchall()
    
    def _get_player_by_id(self, player_id):
        player_id = int(player_id)
        self.cursor.execute("SELECT * FROM nba_players WHERE id = %s", (player_id,))
        player = self.cursor.fetchone()
        return player
    
    def _reformat_player_name(self, player_name):
        player_name = player_name.lower()
        player_name = player_name.capitalize()
        print(player_name)
        return player_name
    
    def _get_player_by_name(self, player_name):
        player_name = player_name.split()
        first_name = self._reformat_player_name(player_name[0])
        last_name = self._reformat_player_name(player_name[1])
        print(f"First name: {first_name}, Last name: {last_name}")

        query = """
        SELECT * FROM nba_players WHERE first_name = %s AND last_name = %s;
        """

        self.cursor.execute(query, (first_name, last_name))
        player = self.cursor.fetchone()
        return player
    
    def _get_random_player(self):
        player_ids = [player['id'] for player in self.players]
        random_player_id = np.random.choice(player_ids)
        random_player = self._get_player_by_id(random_player_id)
        return random_player
    
    def _get_player_name(self, player_id):
        player = self._get_player_by_id(player_id)
        player_name = f"{player['first_name']} {player['last_name']}"
        return player_name
    
    def _get_player_team(self, player_id):
        player = self._get_player(player_id)
        team_id = player['team_id']

        query = """
        SELECT name FROM nba_teams WHERE id = %s;
        """

        self.cursor.execute(query, (team_id,))
        team = self.cursor.fetchone()
        team_name = team['name']
        return team_name
    
    def _compare_players(self, random_player, guess_player):
        """
        Compare all attributes of the random player with the guessed player
        """

        for key in random_player.keys():
            if random_player[key] != guess_player[key]:
                if key == 'id' or key == 'team_id' or key == 'url' or key == 'image_url' or key == 'first_name' or key == 'last_name':
                    continue
                if key == 'position' and (random_player[key] in guess_player[key] or guess_player[key] in random_player[key]):
                    print(f"Partial match: {key}: {random_player[key]} vs {guess_player[key]}")
                else:
                    print(f"{key}: {random_player[key]} vs {guess_player[key]}")
            else:
                print(f"CORRECT: {key}: {random_player[key]} vs {guess_player[key]}")
    
    def game(self):
        player = self._get_random_player()
        player_id = player['id']
        player_name = self._get_player_name(player_id)
        print(player_name)

        print("Welcome to the NBA player guessing game!")
        print("Can you guess the player?")
        guess = input("Enter the player's name: ")

        while guess.lower() != player_name.lower():
            guess_player = self._get_player_by_name(guess)
            print(guess_player)
            if guess_player:
                self._compare_players(player, guess_player)
                print("Incorrect! Try again.")
            else:
                print("Player not found. Try again.")
            guess = input("Enter the player's name: ")
        
        print("Congratulations! You guessed the player correctly!")


    
def main():
    game = guessGame()
    game.game()

if __name__ == "__main__":
    main()

    

