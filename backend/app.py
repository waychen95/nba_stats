from flask import Flask, request, jsonify, redirect, url_for, render_template
from dotenv import load_dotenv
import os
import psycopg2
import psycopg2.extras

app = Flask(__name__)

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

    connection = connection
    cursor = connection.cursor(cursor_factory=psycopg2.extras.DictCursor)
except Exception as e:
    print(f"Error: {e.with_traceback()}")

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/player/<player_id>', methods=['GET'])
def player(player_id):
    player_id = int(player_id)
    cursor.execute("SELECT * FROM nba_players WHERE id = %s", (player_id,))
    player = cursor.fetchone()
    return render_template('player.html', player=player)

@app.route('/players', methods=['GET'])
def players():
    cursor.execute("SELECT * FROM nba_players")
    players = cursor.fetchall()
    return render_template('players.html', players=players)

if __name__ == '__main__':
    app.run(debug=True)