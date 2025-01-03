from flask import Flask, request, jsonify, redirect, url_for, render_template
from flask_cors import CORS
from dotenv import load_dotenv
from flask_mail import Mail, Message
from waitress import serve
import os
import psycopg2
import psycopg2.extras
import numpy as np
import pandas as pd
import json
import requests
import random

app = Flask(__name__)
CORS(app)

# Load environment variables
load_dotenv()

# hostname = os.getenv('HOSTNAME')
# username = os.getenv('USER')
# password = os.getenv('PASSWORD')
# database = os.getenv('DATABASE')
# port = os.getenv('DB_PORT')

# Flask-Mail configuration
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = os.getenv('MAIL_USERNAME')
app.config['MAIL_PASSWORD'] = os.getenv('MAIL_PASSWORD')
app.config['MAIL_DEFAULT_SENDER'] = os.getenv('MAIL_USERNAME')

mail = Mail(app)

def get_db_connection():

    # Connect to the PostgreSQL database
    try:
        connection = psycopg2.connect(
            os.getenv('DATABASE_URL'),
        )
        print("Connected to the database")
        
    except Exception as e:
        print(f"Error: {str(e)}")
        connection = None


    return connection

@app.route('/')
def home():

    return "Hello, World!"

@app.route('/teams', methods=['GET'])
def teams():
    
    connection = get_db_connection()
    cursor = connection.cursor(cursor_factory=psycopg2.extras.DictCursor)
    
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

    cursor.close()
    connection.close()

    return jsonify({'teams': teams})

@app.route('/teams/<team_id>', methods=['GET'])
def get_team(team_id):

    connection = get_db_connection()
    cursor = connection.cursor(cursor_factory=psycopg2.extras.DictCursor)

    team_id = int(team_id)
    query = """
    SELECT * FROM nba_teams WHERE id = %s;
    """
    cursor.execute(query, (team_id,))
    team = cursor.fetchone()
    team = dict(team)

    cursor.close()
    connection.close()

    return jsonify({'team': team})

@app.route('/teams/abbr/<team_abbr>', methods=['GET'])
def get_team_by_abbr(team_abbr):

    connection = get_db_connection()
    cursor = connection.cursor(cursor_factory=psycopg2.extras.DictCursor)

    team_abbr = team_abbr.upper()
    print(team_abbr)
    query = """
    SELECT * FROM nba_teams WHERE name = %s;
    """
    cursor.execute(query, (team_abbr,))
    team = cursor.fetchone()
    team = dict(team)

    cursor.close()
    connection.close()

    return jsonify({'team': team})

@app.route('/teams/<team_id>/players', methods=['GET'])
def get_team_players(team_id):

    connection = get_db_connection()
    cursor = connection.cursor(cursor_factory=psycopg2.extras.DictCursor)

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

    cursor.close()
    connection.close()

    return jsonify({'players': players})

@app.route('/players/<player_id>', methods=['GET'])
def get_player(player_id):

    connection = get_db_connection()
    cursor = connection.cursor(cursor_factory=psycopg2.extras.DictCursor)

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

    cursor.close()
    connection.close()

    return jsonify({'player': player})

@app.route('/players', methods=['GET'])
def players():

    connection = get_db_connection()
    cursor = connection.cursor(cursor_factory=psycopg2.extras.DictCursor)

    order = request.args.get('order', 'asc').lower()
    team = request.args.get('team', None)
    search = request.args.get('search', None)
    page = int(request.args.get('page', 1))
    limit = int(request.args.get('limit', 10))
    active = request.args.get('active', None)

    offset = (page - 1) * limit
    if order not in ['asc', 'desc']:
        order = 'asc'

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
    params = []
    where_clauses = []

    if team:
        where_clauses.append("t.name = %s")
        params.append(team.upper())
    if search:
        if search.includes('+'):
            search = search.replace('+', '')
        search_terms = search.strip().split()
        if len(search_terms) == 2:
            # If there are two words, treat them as first_name and last_name
            where_clauses.append("(p.first_name ILIKE %s AND p.last_name ILIKE %s)")
            params.extend([f'%{search_terms[0]}%', f'%{search_terms[1]}%'])
        else:
            # Otherwise, search in first_name or last_name
            where_clauses.append("(p.full_name ILIKE %s OR p.first_name ILIKE %s OR p.last_name ILIKE %s)")
            params.extend([f'%{search}%', f'%{search}%'])
    if active and active.lower() in ['true', 'false']:
        is_active = active.lower() == 'true'
        if is_active:
            where_clauses.append("p.active = %s")
            params.append(is_active)

    if where_clauses:
        query += " WHERE " + " AND ".join(where_clauses)

    query += f" ORDER BY p.last_name {order} LIMIT %s OFFSET %s"
    params.extend([limit, offset])

    cursor.execute(query, tuple(params))
    players = cursor.fetchall()

    count_query = """
    SELECT COUNT(*)
    FROM nba_players p
    JOIN nba_teams t ON p.team_id = t.id
    """
    if where_clauses:
        count_query += " WHERE " + " AND ".join(where_clauses)

    cursor.execute(count_query, tuple(params[:-2]))  # Exclude LIMIT and OFFSET
    total_players = cursor.fetchone()[0]

    players = [dict(player) for player in players]

    cursor.close()
    connection.close()

    return jsonify({
        'players': players,
        'total': total_players,
        'page': page,
        'limit': limit
    })

@app.route('/all_players', methods=['GET'])
def all_players():

    connection = get_db_connection()
    cursor = connection.cursor(cursor_factory=psycopg2.extras.DictCursor)

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
    players = [dict(player) for player in players]

    cursor.close()
    connection.close()

    return jsonify({'players': players})

@app.route('/well_known_players', methods=['GET'])
def well_known_players():

    connection = get_db_connection()
    cursor = connection.cursor(cursor_factory=psycopg2.extras.DictCursor)

    query = """
    SELECT
        p.*,
        t.name AS team_name,
        t.conference AS team_conference
    FROM nba_players p
    LEFT JOIN (
        SELECT player_id
        FROM nba_player_stats
        GROUP BY player_id
        HAVING COUNT(*) >= 6
    ) AS players_with_more_than_6_stats
    ON p.id = players_with_more_than_6_stats.player_id
    JOIN nba_teams t ON p.team_id = t.id
    WHERE players_with_more_than_6_stats.player_id IS NOT NULL;
    """
    cursor.execute(query)
    players = cursor.fetchall()
    players = [dict(player) for player in players]

    cursor.close()
    connection.close()

    return jsonify({'players': players})

@app.route('/guess_players', methods=['GET'])
def guess_players():

    connection = get_db_connection()
    cursor = connection.cursor(cursor_factory=psycopg2.extras.DictCursor)

    query = """
    SELECT
        p.*,
        t.name AS team_name,
        t.conference AS team_conference
    FROM nba_players p
    LEFT JOIN (
        SELECT player_id
        FROM nba_player_stats
        GROUP BY player_id
        HAVING COUNT(*) >= 7
    ) AS players_with_more_than_7_stats
    ON p.id = players_with_more_than_7_stats.player_id
    JOIN nba_teams t ON p.team_id = t.id
    WHERE players_with_more_than_7_stats.player_id IS NOT NULL;
    """
    cursor.execute(query)
    players = cursor.fetchall()
    players = [dict(player) for player in players]

    cursor.close()
    connection.close()

    return jsonify({'players': players})


@app.route('/players/<player_id>/stats', methods=['GET'])
def player_stats(player_id):

    connection = get_db_connection()
    cursor = connection.cursor(cursor_factory=psycopg2.extras.DictCursor)

    try:
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

        # Convert the stats to a list of dictionaries
        stats = [dict(stat) for stat in stats]

        # Sanitize data: Replace NaN or None with appropriate values
        for stat in stats:
            for key, value in stat.items():
                if value is None or (isinstance(value, float) and np.isnan(value)):
                    stat[key] = None  # Or set a default value if needed, e.g., 0 or "N/A"

        return jsonify({'stats': stats})
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        cursor.close()
        connection.close()
    
@app.route('/api/contact', methods=['POST'])
def contact():

    # Get data from the request
    data = request.get_json()

    # Validate data
    if not data.get('email') or not data.get('message') or not data.get('first_name') or not data.get('last_name'):
        return jsonify({'error': 'All fields are required.'}), 400

    try:
        # Compose email
        msg = Message(
            subject=f"New Contact Form Submission from {data['first_name']} {data['last_name']}",
            recipients=[os.getenv('MAIL_USERNAME')],
            body=f"Message from {data['first_name']} {data['last_name']} ({data['email']}):\n\n{data['message']}"
        )

        # Send email
        mail.send(msg)
        return jsonify({'message': 'Message sent successfully!'}), 200

    except Exception as e:
        print(e)
        return jsonify({'error': 'Failed to send message.'}), 500
    
def run_app():
    port = int(os.environ.get("PORT", 50100))
    serve(app, host='0.0.0.0', port=port, threads=2)

if __name__ == '__main__':
    run_app()