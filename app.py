"""
Smart Election Voting System - Flask Application
Face Recognition based Voting Application
"""

from flask import Flask, render_template, request, redirect, url_for, session, flash
import sqlite3
import hashlib
import os
from functools import wraps

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', os.urandom(24))  # Secure secret key for sessions

# Register the JSON REST API (used by the React frontend).
try:
    from api import api_bp
    app.register_blueprint(api_bp)
except ImportError:
    # The migration keeps the original template-based routes working even
    # if the API module fails to load for some reason.
    pass

# Optional narrow CORS for development only. In production we prefer same-origin
# (React build served by Flask) and keep this disabled.
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

# Auto-create public link (for sharing) - only in local development
import sys
if not any('gunicorn' in arg for arg in sys.argv):
    try:
        from pyngrok import ngrok
        public_url = ngrok.connect(5000)
        print(f"\n🌐 PUBLIC LINK: {public_url}")
        print(f"📱 Share this link to access the app remotely!\n")
    except:
        print("\n💡 Tip: Install pyngrok to create a public link:")
        print("   pip install pyngrok\n")

# Database configuration
DB_PATH = "voting.db"

# ----------------------------
# DATABASE FUNCTIONS
# ----------------------------

def init_db():
    """Initialize database with complete user schema"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Users table - stores voter registration data
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
    
    # Votes table - stores all votes
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS votes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            voter_id INTEGER,
            candidate TEXT NOT NULL,
            voted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (voter_id) REFERENCES users (id)
        )
    """)
    
    # Candidates table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS candidates (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            party TEXT NOT NULL,
            symbol TEXT,
            votes INTEGER DEFAULT 0
        )
    """)
    
    # Insert default candidates if not exist
    cursor.execute("SELECT COUNT(*) FROM candidates")
    if cursor.fetchone()[0] == 0:
        default_candidates = [
            ("Bharatiya Janata Party", "BJP", "Lotus"),
            ("Indian National Congress", "INC", "Hand"),
            ("Bahujan Samaj Party", "BSP", "Elephant"),
            ("Communist Party of India (Marxist)", "CPIM", "Hammer"),
            ("Aam Aadmi Party", "AAP", "Broom"),
            ("National People's Party", "NPP", "Star")
        ]
        cursor.executemany(
            "INSERT INTO candidates (name, party, symbol, votes) VALUES (?, ?, ?, 0)",
            default_candidates
        )
    
    conn.commit()
    conn.close()
    print("[OK] Database initialized successfully!")


def get_db_connection():
    """Get database connection"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def hash_password(password):
    """Hash password using SHA256"""
    return hashlib.sha256(password.encode()).hexdigest()


# ----------------------------
# LOGIN REQUIRED DECORATOR
# ----------------------------

def login_required(f):
    """Decorator to require login"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please login first!', 'error')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function


# ----------------------------
# ROUTES
# ----------------------------

@app.route('/')
def index():
    """Home page - redirects to home"""
    return redirect(url_for('splash'))


@app.route('/splash')
def splash():
    """Splash screen page"""
    return render_template('splash.html')


@app.route('/home')
def home():
    """Home page"""
    return render_template('home.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    """Login route"""
    if request.method == 'POST':
        voterid = request.form.get('voterid', '').strip()
        password = request.form.get('password', '')
        
        if not voterid or not password:
            flash('Please enter Voter ID and Password!', 'error')
            return render_template('login.html')
        
        hashed_password = hash_password(password)
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Check if user exists (by voterid or aadhaar)
        cursor.execute(
            "SELECT id, name, voterid, aadhaar FROM users WHERE (voterid = ? OR aadhaar = ?) AND password = ?",
            (voterid, voterid, hashed_password)
        )
        user = cursor.fetchone()
        conn.close()
        
        if user:
            session['user_id'] = user['id']
            session['user_name'] = user['name']
            session['voterid'] = user['voterid']
            flash(f'Welcome {user["name"]}!', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid Voter ID/Aadhaar or Password!', 'error')
            return render_template('login.html')
    
    return render_template('login.html')


@app.route('/signup', methods=['GET', 'POST'])
def signup():
    """Registration route"""
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        dob = request.form.get('dob', '').strip()
        gender = request.form.get('gender', '').strip()
        aadhaar = request.form.get('aadhaar', '').strip()
        voterid = request.form.get('voterid', '').strip()
        mobile = request.form.get('mobile', '').strip()
        email = request.form.get('email', '').strip()
        address = request.form.get('address', '').strip()
        country = request.form.get('country', '').strip()
        password = request.form.get('password', '').strip()
        
        # Validation
        if not all([name, dob, gender, aadhaar, voterid, mobile, email, address, country, password]):
            flash('All fields are required!', 'error')
            return render_template('signup.html')
        
        if len(aadhaar) != 12 or not aadhaar.isdigit():
            flash('Aadhaar must be 12 digits!', 'error')
            return render_template('signup.html')
        
        if len(password) < 6:
            flash('Password must be at least 6 characters!', 'error')
            return render_template('signup.html')
        
        hashed_password = hash_password(password)
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                INSERT INTO users (name, dob, gender, aadhaar, voterid, mobile, email, address, country, password)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (name, dob, gender, aadhaar, voterid, mobile, email, address, country, hashed_password))
            
            # Get the newly created user id
            user_id = cursor.lastrowid
            
            conn.commit()
            conn.close()
            
            # Store user_id in session for face capture
            session['user_id'] = user_id
            session['user_name'] = name
            session['just_registered'] = True  # Flag to indicate this is registration flow
            
            flash('Registration successful! Please capture your profile photo to continue.', 'success')
            return redirect(url_for('face_verify'))
            
        except sqlite3.IntegrityError:
            flash('Aadhaar or Voter ID already registered!', 'error')
            conn.close()
            return render_template('signup.html')
    
    return render_template('signup.html')


@app.route('/dashboard')
@login_required
def dashboard():
    """Dashboard - after login"""
    user_name = session.get('user_name', 'User')
    return render_template('dashboard.html', user_name=user_name)


@app.route('/face_verify')
@login_required
def face_verify():
    """Face verification page"""
    # Check if this is being called after registration (profile photo capture)
    is_registration = session.get('just_registered', False)
    return render_template('face_verify.html', is_registration=is_registration)


@app.route('/face_verify_process', methods=['POST'])
@login_required
def face_verify_process():
    """Process face verification"""
    import base64
    import os
    
    try:
        data = request.get_json()
        image_data = data.get('image', '')
        
        if not image_data:
            return {'success': False, 'message': 'No image provided'}
        
        # Extract base64 data
        if 'base64,' in image_data:
            image_data = image_data.split('base64,')[1]
        
        # Create user folder if not exists (in static folder for serving)
        user_id = session.get('user_id')
        user_folder = os.path.join('static', 'data', str(user_id))
        os.makedirs(user_folder, exist_ok=True)
        
        # Save the captured face
        face_file = os.path.join(user_folder, 'face.png')
        with open(face_file, 'wb') as f:
            f.write(base64.b64decode(image_data))
        
        # Store verification status in session
        session['face_verified'] = True
        session['face_captured'] = True
        
        # Clear the just_registered flag if it was set
        if session.get('just_registered'):
            session.pop('just_registered', None)
        
        return {'success': True, 'message': 'Face verified successfully'}
        
    except Exception as e:
        print(f"Face verification error: {e}")
        return {'success': False, 'message': str(e)}


@app.route('/vote', methods=['GET', 'POST'])
@login_required
def vote():
    """Vote page - requires face verification first"""
    # Check if face has been verified
    if not session.get('face_verified', False):
        flash('Please verify your face first!', 'error')
        return redirect(url_for('face_verify'))
    
    if request.method == 'POST':
        candidate = request.form.get('candidate')
        
        if not candidate:
            flash('Please select a candidate!', 'error')
            return redirect(url_for('vote'))
        
        user_id = session.get('user_id')
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Check if user already voted
        cursor.execute("SELECT has_voted FROM users WHERE id = ?", (user_id,))
        user = cursor.fetchone()
        
        if user['has_voted'] == 1:
            flash('You have already voted!', 'error')
            conn.close()
            return redirect(url_for('dashboard'))
        
        # Record vote
        cursor.execute("INSERT INTO votes (voter_id, candidate) VALUES (?, ?)", (user_id, candidate))
        cursor.execute("UPDATE users SET has_voted = 1 WHERE id = ?", (user_id,))
        cursor.execute("UPDATE candidates SET votes = votes + 1 WHERE party = ?", (candidate,))
        
        # Store voted party in session for success page
        session['last_voted_party'] = candidate
        
        conn.commit()
        conn.close()
        
        flash('Vote recorded successfully!', 'success')
        return redirect(url_for('vote_success'))
    
    # GET request - show candidates
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT name, party, symbol FROM candidates")
    candidates = cursor.fetchall()
    conn.close()
    
    return render_template('vote.html', candidates=candidates)


@app.route('/vote_success')
@login_required
def vote_success():
    """Vote success page"""
    party = session.get('last_voted_party', 'BJP')
    return render_template('vote_success.html', party=party)


@app.route('/profile')
@login_required
def profile():
    """User profile page"""
    user_id = session.get('user_id')
    
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT name, aadhaar, voterid, email, mobile, address, dob, gender, country, has_voted
        FROM users WHERE id = ?
    """, (user_id,))
    user = cursor.fetchone()
    conn.close()
    
    # Check if user has a profile photo
    import os
    face_path = os.path.join('static', 'data', str(user_id), 'face.png')
    user_face_exists = os.path.exists(face_path)
    
    # Also check old location for backward compatibility
    old_face_path = os.path.join('data', str(user_id), 'face.png')
    if not user_face_exists and os.path.exists(old_face_path):
        # Move to new location
        os.makedirs(os.path.dirname(face_path), exist_ok=True)
        import shutil
        shutil.move(old_face_path, face_path)
        user_face_exists = True
    
    if user:
        return render_template('profile.html', user=user, user_id=user_id, user_face_exists=user_face_exists)
    else:
        flash('User not found!', 'error')
        return redirect(url_for('login'))


@app.route('/results')
@login_required
def results():
    """View voting results"""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT party, name, symbol, votes FROM candidates ORDER BY votes DESC")
    results = cursor.fetchall()
    conn.close()
    
    total_votes = sum(r['votes'] for r in results)
    
    return render_template('results.html', results=results, total_votes=total_votes)


@app.route('/logout')
def logout():
    """Logout route"""
    session.clear()
    flash('Logged out successfully!', 'success')
    return redirect(url_for('home'))


# ----------------------------
# VIDEO FEED PLACEHOLDER
# ----------------------------

@app.route('/video_feed')
def video_feed():
    """Placeholder for video feed - in production, integrate with face recognition"""
    # This would return video stream from camera
    # For now, redirect to a placeholder or return 404
    return "Video feed not implemented yet. Use face verification button to proceed."


# ----------------------------
# ERROR HANDLERS
# ----------------------------

@app.errorhandler(404)
def page_not_found(e):
    # If the React production build is present, let it handle 404s so that
    # client-side routing keeps working on hard refresh.
    if os.path.exists('frontend/dist/index.html'):
        try:
            from flask import send_from_directory

            return send_from_directory('frontend/dist', 'index.html')
        except Exception:
            pass
    return render_template('error.html', error='Page not found'), 404


@app.errorhandler(500)
def internal_error(e):
    return render_template('error.html', error='Internal server error'), 500


# ----------------------------
# OPTIONAL: SERVE REACT BUILD
# ----------------------------

def _register_react_static():
    """If the React production build exists, mount it at / so the SPA is
    served by Flask. This is only used in deploy; during local development
    React is served by Vite on :5173 and proxies /api to Flask."""
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
        # SPA fallback so client-side routes work on hard refresh.
        return send_from_directory(build_dir, 'index.html')


_register_react_static()

if __name__ == '__main__':
    # Initialize database
    init_db()
    
    # Run Flask app
    print("\n" + "="*50)
    print("Smart Voting System Starting...")
    print("Visit: http://127.0.0.1:5000")
    print("="*50 + "\n")
    
    # Use debug=False for production
    debug_mode = os.environ.get('FLASK_DEBUG', 'False').lower() == 'true'
    app.run(debug=debug_mode, host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))

