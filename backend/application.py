from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_mail import Mail, Message
from dotenv import load_dotenv
import os
import psycopg2
import psycopg2.extras
import numpy as np
from datetime import datetime, timedelta

from collections import deque
from chatbot.nbadle_chatbot import NBAdleChatbot

app = Flask(__name__)
application = app
CORS(app, resources={r"/*": {"origins": ["http://localhost:5173", r"https://.*\.vercel\.app",]}})

# Load environment variables
load_dotenv()

# Flask-Mail configuration
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = os.getenv('MAIL_USERNAME')
app.config['MAIL_PASSWORD'] = os.getenv('MAIL_PASSWORD')
app.config['MAIL_DEFAULT_SENDER'] = os.getenv('MAIL_USERNAME')

mail = Mail(app)

# Initialize the chatbot
CHATBOT = NBAdleChatbot()

SESSION_HISTORY: dict[str, deque] = {}
SESSION_TIMEOUT = timedelta(minutes=5)
MAX_TURNS = 3
MAX_HISTORY_CHARS = 2500

# @app.before_first_request
# def initialize_chatbot():
#     global CHATBOT
#     if CHATBOT is None:
#         print("Initializing NBAdleChatbot...")
#         CHATBOT = NBAdleChatbot()
#         print("NBAdleChatbot initialized.")

def get_session_history(session_id: str) -> deque:
    cleanup_old_sessions()
    
    if session_id not in SESSION_HISTORY:
        SESSION_HISTORY[session_id] = {
            "history": deque(maxlen=MAX_TURNS * 2),
            "last_access": datetime.now()
        }
    
    SESSION_HISTORY[session_id]["last_access"] = datetime.now()
    return SESSION_HISTORY[session_id]["history"]

def cleanup_old_sessions():
    now = datetime.now()
    expired = [
        sid for sid, data in SESSION_HISTORY.items()
        if now - data["last_access"] > SESSION_TIMEOUT
    ]
    for sid in expired:
        del SESSION_HISTORY[sid]

def format_history(history: deque, max_chars: int = MAX_HISTORY_CHARS) -> str:
    lines = []
    for msg in history:
        role = "User" if msg.get("role") == "user" else "Assistant"
        lines.append(f"{role}: {msg.get('text','')}")
    s = "\n".join(lines)

    if len(s) > max_chars:
        s = s[-max_chars:]
        cut = s.find("\n")
        if cut != -1:
            s = s[cut + 1 :]
    return s

# def get_db_connection():
#     """
#     Connect to PostgreSQL using either DATABASE_URL or individual environment variables.
#     """
#     db_url = os.getenv('DATABASE_URL')

#     try:
#         if db_url:
#             # Use single DATABASE_URL if available
#             connection = psycopg2.connect(db_url)
#         else:
#             hostname = os.getenv('HOSTNAME')
#             username = os.getenv('USER')
#             password = os.getenv('PASSWORD')
#             database = os.getenv('DATABASE')
#             port = os.getenv('PORT', 5432)

#             # Fall back to individual environment variables
#             if not all([hostname, username, password, database]):
#                 raise ValueError("Database connection variables are not fully set")

#             connection = psycopg2.connect(
#                 host=hostname,
#                 user=username,
#                 password=password,
#                 dbname=database,
#                 port=port
#             )

#         print("Connected to the database")
#         return connection

#     except Exception as e:
#         print(f"Database connection error: {str(e)}")
#         return None

def get_db_connection():
    db_url = os.getenv("DATABASE_URL")
    if not db_url:
        raise ValueError("DATABASE_URL is not set")

    return psycopg2.connect(db_url)


@app.route('/')
def home():

    return "Hello!"

@app.route("/test-db")
def test_db():
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT version();")
        result = cur.fetchone()
        cur.close()
        conn.close()
        return {"db": "ok", "version": result}
    except Exception as e:
        return {"db": "error", "message": str(e)}
    
@app.route("/chat/health", methods=["GET"])
def chat_health():
    return jsonify({
        "status": "ok",
        "docs": len(getattr(CHATBOT, "docs", []))
    })
    
@app.route("/chat", methods=["POST"])
def chat():

    if CHATBOT is None:
        return jsonify({"error": "Chatbot not initialized"}), 503
    
    data = request.get_json(silent=True) or {}
    message = (data.get("message") or "").strip()
    session_id = data.get("session_id")
    if not session_id:
        return jsonify({"error": "session_id is required"}), 400

    if not message:
        return jsonify({"error": "message is required"}), 400

    history = get_session_history(session_id)

    history_text = format_history(history)

    history.append({"role": "user", "text": message})

    try:
        answer, metadata = CHATBOT.answer_question(message, history=history_text)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

    history.append({"role": "assistant", "text": answer})

    response =  {
        "session_id": session_id,
        "answer": answer,
    }

    if metadata:
        response['metadata'] = metadata if "sorry" not in answer.lower() else {}

    return jsonify(response)

@app.route('/teams', methods=['GET'])
def teams():
    
    try:
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

        return jsonify({'teams': teams})
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        cursor.close()
        connection.close()

@app.route('/teams/<team_id>', methods=['GET'])
def get_team(team_id):

    try:
        connection = get_db_connection()
        cursor = connection.cursor(cursor_factory=psycopg2.extras.DictCursor)

        team_id = int(team_id)
        query = """
        SELECT * FROM nba_teams WHERE id = %s;
        """
        cursor.execute(query, (team_id,))
        team = cursor.fetchone()
        team = dict(team)
        return jsonify({'team': team})
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        cursor.close()
        connection.close()

@app.route('/teams/abbr/<team_abbr>', methods=['GET'])
def get_team_by_abbr(team_abbr):

    try:
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
        return jsonify({'team': team})
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        cursor.close()
        connection.close()

@app.route('/teams/<team_id>/players', methods=['GET'])
def get_team_players(team_id):

    try:
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
        return jsonify({'players': players})
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        cursor.close()
        connection.close()

@app.route('/players/<player_id>', methods=['GET'])
def get_player(player_id):

    try:
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
        return jsonify({'player': player})
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        cursor.close()
        connection.close()

@app.route('/players', methods=['GET'])
def players():

    try:
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
            search_pattern = f"%{search.strip()}%"
            # Search either in first_name, last_name, or full_name (first + last)
            where_clauses.append("""
                (p.first_name ILIKE %s OR 
                p.last_name ILIKE %s OR 
                (p.first_name || ' ' || p.last_name) ILIKE %s)
            """)
            params.extend([search_pattern, search_pattern, search_pattern])
            # search_terms = search.strip().split()
            # if len(search_terms) == 2:
            #     # If there are two words, treat them as first_name and last_name
            #     where_clauses.append("(p.first_name ILIKE %s AND p.last_name ILIKE %s)")
            #     params.extend([f'%{search_terms[0]}%', f'%{search_terms[1]}%'])
            # else:
            #     # Otherwise, search in first_name or last_name
            #     where_clauses.append("""
            #         (p.first_name ILIKE %s OR 
            #         p.last_name ILIKE %s OR 
            #         (p.first_name || ' ' || p.last_name) ILIKE %s)
            #     """)
            #     params.extend([f'%{search}%', f'%{search}%', f'%{search}%'])
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

        return jsonify({
            'players': players,
            'total': total_players,
            'page': page,
            'limit': limit
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        cursor.close()
        connection.close()

@app.route('/all_players', methods=['GET'])
def all_players():

    try:
        connection = get_db_connection()
        cursor = connection.cursor(cursor_factory=psycopg2.extras.DictCursor)

        active = request.args.get('active', None)

        params = []
        where_clauses = []

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

        if active and active.lower() in ['true', 'false']:
            is_active = active.lower() == 'true'
            if is_active:
                where_clauses.append("p.active = %s")
                params.append(is_active)
        
        if where_clauses:
            query += " WHERE " + " AND ".join(where_clauses)

        query += ";"

        cursor.execute(query, tuple(params))

        players = cursor.fetchall()
        players = [dict(player) for player in players]
        return jsonify({'players': players})
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        cursor.close()
        connection.close()

@app.route('/well_known_players', methods=['GET'])
def well_known_players():

    try:
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
        return jsonify({'players': players})
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        cursor.close()
        connection.close()

@app.route('/guess_players', methods=['GET'])
def guess_players():
    
    try:
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
        WHERE players_with_more_than_7_stats.player_id IS NOT NULL AND p.image_url != 'https://cdn.nba.com/headshots/nba/latest/260x190/fallback.png';
        """
        cursor.execute(query)
        players = cursor.fetchall()
        players = [dict(player) for player in players]
        return jsonify({'players': players})
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        cursor.close()
        connection.close()


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
    app.run(host='0.0.0.0', port=3000)

if __name__ == '__main__':
    run_app()
