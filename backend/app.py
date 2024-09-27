from flask import Flask, request, jsonify, redirect, url_for, render_template
from flask_cors import CORS
from dotenv import load_dotenv
import os
import psycopg2
import psycopg2.extras
import numpy as np
import pandas as pd
import json
import requests
import random

app = Flask(__name__)
CORS(app, origins=["http://localhost:5173"])

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
    print(f"Error: {str(e)}")

@app.route('/')
def home():
    return "Hello, World!"

@app.route('/teams', methods=['GET'])
def teams():

    order = request.args.get('order', 'asc').lower()
    order = 'asc' if order not in ['asc', 'desc'] else order

    conference = request.args.get('conference', None)

    base_query = """
    SELECT * FROM nba_teams
    """

    if conference:
        query = base_query + """
        WHERE conference = %s
        ORDER BY full_name {};
        """.format(order)

        cursor.execute(query, (conference,))

    else:
        query = base_query + f"ORDER BY full_name {order};"
        cursor.execute(query)

    print(query)

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

@app.route('/teams/abbr/<team_abbr>', methods=['GET'])
def get_team_by_abbr(team_abbr):
    team_abbr = team_abbr.upper()
    print(team_abbr)
    query = """
    SELECT * FROM nba_teams WHERE name = %s;
    """
    cursor.execute(query, (team_abbr,))
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
        t.name AS team_name,
        t.conference AS team_conference
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
    order = request.args.get('order', 'asc')
    team = request.args.get('team', None)
    search = request.args.get('search', None)
    page = int(request.args.get('page', 1))  # Default to page 1
    limit = int(request.args.get('limit', 10))  # Default to 10 players per page
    offset = (page - 1) * limit

    # Base query
    query = """
    SELECT 
        p.*, 
        t.name AS team_name,
        t.conference AS team_conference
    FROM 
        nba_players p
    JOIN 
        nba_teams t 
    ON 
        p.team_id = t.id
    """
    
    if page and limit:
        # Parameters for query filtering
        params = []
        
        # Add filtering by team if provided
        if team:
            query += " WHERE t.name = %s"
            params.append(team.upper())
        
        # Add search filter if provided
        if search:
            if team:
                query += " AND (p.first_name ILIKE %s OR p.last_name ILIKE %s)"
            else:
                query += " WHERE (p.first_name ILIKE %s OR p.last_name ILIKE %s)"
            params.extend([f'%{search}%', f'%{search}%'])
        
        # Add ordering and pagination
        query += f" ORDER BY p.last_name {order} LIMIT %s OFFSET %s;"
        params.extend([limit, offset])
        
        # Execute the query to get paginated players
        cursor.execute(query, tuple(params))
        players = cursor.fetchall()

    # Query to get the total number of players without LIMIT and OFFSET for pagination calculation
    count_query = """
    SELECT COUNT(*)
    FROM nba_players p
    JOIN nba_teams t ON p.team_id = t.id
    """
    
    if team:
        count_query += " WHERE t.name = %s"
        count_params = [team.upper()]
    else:
        count_params = []

    if search:
        if team:
            count_query += " AND (p.first_name ILIKE %s OR p.last_name ILIKE %s)"
            count_params.extend([f'%{search}%', f'%{search}%'])
        else:
            count_query += " WHERE (p.first_name ILIKE %s OR p.last_name ILIKE %s)"
            count_params.extend([f'%{search}%', f'%{search}%'])

    # Execute the count query to get the total number of players
    cursor.execute(count_query, tuple(count_params))
    total_players = cursor.fetchone()[0]  # Total count of players
    
    # Convert fetched players to a dictionary
    players = [dict(player) for player in players]

    # Return players and total number for pagination
    return jsonify({
        'players': players,
        'total': total_players,
        'page': page,
        'limit': limit
    })


@app.route('/players/random', methods=['GET'])
def random_player():
    query = """
    SELECT 
        p.*, 
        t.name AS team_name,
        t.conference AS team_conference
    FROM 
        nba_players p
    JOIN 
        nba_teams t 
    ON 
        p.team_id = t.id;
    """
    cursor.execute(query)
    players = cursor.fetchall()
    random_player = random.choice(players)
    random_player = dict(zip([desc[0] for desc in cursor.description], random_player))
    return jsonify({'random_player': random_player})

@app.route('/players/<player_id>/stats', methods=['GET'])
def player_stats(player_id):
    player_id = int(player_id)
    query = """
    SELECT 
        ps.*,
        p.first_name,
        p.last_name,
        t.name AS team_name
    FROM 
        nba_player_stats ps
    JOIN 
        nba_players p 
    ON 
        ps.player_id = p.id
    JOIN
        nba_teams t
    ON
        ps.team_id = t.id
    WHERE
        ps.player_id = %s
    ORDER BY ps.year ASC;
    """
    cursor.execute(query, (player_id,))
    stats = cursor.fetchall()
    stats = [dict(stat) for stat in stats]
    return jsonify({'stats': stats})

if __name__ == '__main__':
    app.run(debug=True)