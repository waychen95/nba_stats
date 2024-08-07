from flask import Flask, request, jsonify, redirect, url_for, render_template
from flask_cors import CORS
from dotenv import load_dotenv
import os
import psycopg2
import psycopg2.extras

app = Flask(__name__)
CORS(app)

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
    return "Hello, World!"

@app.route('/teams', methods=['GET'])
def teams():
    query = """
    SELECT * FROM nba_teams;
    """
    cursor.execute(query)
    teams = cursor.fetchall()
    teams = [dict(team) for team in teams]
    return jsonify({'teams': teams})

@app.route('/teams/<team_id>', methods=['GET'])
def get_team(team_id):
    team_id = int(team_id)
    query = """
    SELECT * FROM nba_teams WHERE id = %s;
    """
    cursor.execute(query, (team_id,))
    team = cursor.fetchone()
    team = dict(team)
    return jsonify({'team': team})

@app.route('/teams/<team_id>/players', methods=['GET'])
def get_team_players(team_id):
    team_id = int(team_id)
    query = """
    SELECT
        p.*,
        t.name AS team_name
    FROM
        nba_players p
    JOIN
        nba_teams t
    ON
        p.team_id = t.id
    WHERE
        p.team_id = %s;
    """
    cursor.execute(query, (team_id,))
    players = cursor.fetchall()
    players = [dict(player) for player in players]
    return jsonify({'players': players})

@app.route('/players/<player_id>', methods=['GET'])
def get_player(player_id):
    player_id = int(player_id)
    query = """
    SELECT
        p.*,
        t.name AS team_name
    FROM
        nba_players p
    JOIN
        nba_teams t
    ON
        p.team_id = t.id
    WHERE
        p.id = %s;
    """
    cursor.execute(query, (player_id,))
    player = cursor.fetchone()
    player = dict(player)
    return jsonify({'player': player})

@app.route('/players', methods=['GET'])
def players():
    query = """
    SELECT 
        p.*, 
        t.name AS team_name
    FROM 
        nba_players p
    JOIN 
        nba_teams t 
    ON 
        p.team_id = t.id;
    """
    cursor.execute(query)
    players = cursor.fetchall()
    players = [dict(player) for player in players]
    return jsonify({'players': players})

if __name__ == '__main__':
    app.run(debug=True)