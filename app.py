"""
Smart Election Voting System - Flask application entry point.

This module wires the REST API blueprint (api.py), initializes the
SQLite schema, optionally enables narrow CORS for local development,
and serves the React production build when one exists.

The legacy Flask-template routes have been removed: React (under
frontend/) is the only frontend.
"""

from flask import Flask
import sqlite3
import hashlib
import os

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', os.urandom(24))

try:
    from api import api_bp
    app.register_blueprint(api_bp)
except ImportError:
    pass

if os.environ.get('ENABLE_CORS', '').lower() in ('1', 'true', 'yes'):
    try:
        from flask_cors import CORS
        CORS(
            app,
            resources={r"/api/*": {"origins": os.environ.get('CORS_ORIGINS', 'http://127.0.0.1:5173')}},
            supports_credentials=True,
        )
    except ImportError:
        print("[warn] flask-cors not installed; CORS disabled.")

import sys
if not any('gunicorn' in arg for arg in sys.argv):
    try:
        from pyngrok import ngrok
        public_url = ngrok.connect(5000)
        print(f"\n[ngrok] PUBLIC LINK: {public_url}")
    except Exception:
        print("\n[ngrok] not available; install pyngrok for a public link.")

DB_PATH = "voting.db"


def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            dob TEXT,
            gender TEXT,
            aadhaar TEXT UNIQUE,
            voterid TEXT UNIQUE,
            mobile TEXT,
            email TEXT,
            address TEXT,
            country TEXT,
            password TEXT NOT NULL,
            face_encoding TEXT,
            has_voted INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS votes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            voter_id INTEGER,
            candidate TEXT NOT NULL,
            voted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (voter_id) REFERENCES users (id)
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS candidates (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            party TEXT NOT NULL,
            symbol TEXT,
            votes INTEGER DEFAULT 0
        )
    """)

    cursor.execute("SELECT COUNT(*) FROM candidates")
    if cursor.fetchone()[0] == 0:
        default_candidates = [
            ("Bharatiya Janata Party", "BJP", "Lotus"),
            ("Indian National Congress", "INC", "Hand"),
            ("Bahujan Samaj Party", "BSP", "Elephant"),
            ("Communist Party of India (Marxist)", "CPIM", "Hammer"),
            ("Aam Aadmi Party", "AAP", "Broom"),
            ("National People's Party", "NPP", "Star"),
        ]
        cursor.executemany(
            "INSERT INTO candidates (name, party, symbol, votes) VALUES (?, ?, ?, 0)",
            default_candidates,
        )

    conn.commit()
    conn.close()
    print("[OK] Database initialized successfully!")


def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()


@app.errorhandler(404)
def page_not_found(e):
    return _spa_or_json("Page not found", 404)


@app.errorhandler(500)
def internal_error(e):
    return _spa_or_json("Internal server error", 500)


def _spa_or_json(message, status):
    from flask import jsonify, send_from_directory

    if os.path.exists('frontend/dist/index.html'):
        return send_from_directory('frontend/dist', 'index.html'), status
    return jsonify({"error": message, "message": message}), status


def _register_react_static():
    """Mount the React production build at / when present.

    During local development the React dev server runs on :5173 and Vite
    proxies /api/* and /static/* to Flask. In production, gunicorn serves
    Flask and Flask serves the compiled SPA, so the entire experience
    runs from a single origin.
    """
    build_dir = os.path.join('frontend', 'dist')
    if not os.path.exists(os.path.join(build_dir, 'index.html')):
        return

    from flask import send_from_directory

    @app.route('/')
    def _spa_root():
        return send_from_directory(build_dir, 'index.html')

    @app.route('/<path:path>')
    def _spa_assets(path):
        full = os.path.join(build_dir, path)
        if os.path.isfile(full):
            return send_from_directory(build_dir, path)
        return send_from_directory(build_dir, 'index.html')


_register_react_static()


if __name__ == '__main__':
    init_db()
    print("\n" + "=" * 50)
    print("Smart Voting System Starting...")
    print("Visit: http://127.0.0.1:5000")
    print("=" * 50 + "\n")
    debug_mode = os.environ.get('FLASK_DEBUG', 'False').lower() == 'true'
    app.run(debug=debug_mode, host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))