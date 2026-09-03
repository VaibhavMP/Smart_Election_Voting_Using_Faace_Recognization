"""
Backend smoke test for the new /api blueprint.

Runs the Flask app under a test client, using a fresh SQLite database,
without requiring the heavy ML stack (cv2 / sklearn / numpy).

Covers:
  - health
  - register / login / me / logout
  - face register + verify
  - candidates + vote + duplicate vote blocked
  - results + profile

Run:  python smoke_test.py
"""
import base64
import json
import os
import shutil
import sqlite3
import sys
import tempfile
import types

# ---------------------------------------------------------------------------
# 1) Make a temp DB available BEFORE we import app.
# ---------------------------------------------------------------------------
TMPDIR = tempfile.mkdtemp(prefix="svote_smoke_")
TEST_DB = os.path.join(TMPDIR, "voting.db")

# Patch the DB_PATH constant by pre-importing a stub "app" module that
# provides the symbols api.py imports.
app_stub = types.ModuleType("app")


def _init_db():
    conn = sqlite3.connect(TEST_DB)
    cur = conn.cursor()
    cur.execute(
        """
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
        """
    )
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS votes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            voter_id INTEGER,
            candidate TEXT NOT NULL,
            voted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (voter_id) REFERENCES users (id)
        )
        """
    )
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS candidates (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            party TEXT NOT NULL,
            symbol TEXT,
            votes INTEGER DEFAULT 0
        )
        """
    )
    cur.execute("SELECT COUNT(*) FROM candidates")
    if cur.fetchone()[0] == 0:
        cur.executemany(
            "INSERT INTO candidates (name, party, symbol, votes) VALUES (?, ?, ?, 0)",
            [
                ("Bharatiya Janata Party", "BJP", "Lotus"),
                ("Indian National Congress", "INC", "Hand"),
                ("Aam Aadmi Party", "AAP", "Broom"),
            ],
        )
    conn.commit()
    conn.close()


def _get_db_connection():
    conn = sqlite3.connect(TEST_DB)
    conn.row_factory = sqlite3.Row
    return conn


def _hash_password(p):
    import hashlib

    return hashlib.sha256(p.encode()).hexdigest()


app_stub.DB_PATH = TEST_DB
app_stub.init_db = _init_db
app_stub.get_db_connection = _get_db_connection
app_stub.hash_password = _hash_password
sys.modules["app"] = app_stub

# ---------------------------------------------------------------------------
# 2) Build a Flask app with the API blueprint and no template routes.
# ---------------------------------------------------------------------------
import flask

flask_app = flask.Flask(__name__)
flask_app.secret_key = "test-secret"
flask_app.config.update(TESTING=True, SECRET_KEY="test-secret")

# Make sure app.py module loads without executing its __main__ block.
import importlib.util

spec = importlib.util.spec_from_file_location("app_main", "app.py")
app_main = importlib.util.module_from_spec(spec)
app_main.__name__ = "app_main"
# Prevent app.py's __main__ block from running by short-circuiting.
import builtins as _bi

_orig_open = _bi.open  # noqa: F841

try:
    # Skip the heavy top-level side-effects (ngrok etc.) by importing api only.
    from api import api_bp
except Exception as e:
    print(f"[FAIL] api.py import failed: {e}")
    sys.exit(1)

flask_app.register_blueprint(api_bp)

# Ensure the test DB has the schema.
_init_db()


# ---------------------------------------------------------------------------
# 3) Tests
# ---------------------------------------------------------------------------
def _post(c, path, payload):
    return c.post(path, data=json.dumps(payload), content_type="application/json")


def _img_b64():
    # 1x1 transparent PNG
    return "data:image/png;base64," + base64.b64encode(
        b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01"
        b"\x08\x06\x00\x00\x00\x1f\x15\xc4\x89\x00\x00\x00\rIDATx\x9cc```\x00"
        b"\x00\x00\x04\x00\x01[\xcd\xc9\xd6\x00\x00\x00\x00IEND\xaeB`\x82"
    ).decode()


results = []


def report(name, ok, detail=""):
    tag = "PASS" if ok else "FAIL"
    print(f"[{tag}] {name} {detail}")
    results.append((ok, name, detail))


with flask_app.test_client() as c:
    # Health
    r = c.get("/api/health")
    report("health", r.status_code == 200 and r.get_json()["status"] == "ok",
           f"status={r.status_code}")

    # Register valid
    payload = {
        "name": "Test User",
        "dob": "1990-01-01",
        "gender": "Male",
        "aadhaar": "123456789012",
        "voterid": "VOT123",
        "mobile": "9876543210",
        "email": "test@example.com",
        "address": "Some Street",
        "country": "India",
        "password": "secret123",
    }
    r = _post(c, "/api/auth/register", payload)
    report("register.valid", r.status_code == 200 and r.get_json().get("success"),
           f"status={r.status_code}")

    # Register duplicate aadhaar
    r = _post(c, "/api/auth/register", payload)
    report("register.duplicate_aadhaar", r.status_code == 409,
           f"status={r.status_code}")

    # Register invalid aadhaar
    bad = dict(payload, aadhaar="12", voterid="VOT999")
    r = _post(c, "/api/auth/register", bad)
    report("register.invalid_aadhaar", r.status_code == 400,
           f"status={r.status_code}")

    # Register missing fields
    r = _post(c, "/api/auth/register", {})
    report("register.missing_fields", r.status_code == 400,
           f"status={r.status_code}")

    # me after register
    r = c.get("/api/auth/me")
    report("me.after_register", r.status_code == 200 and r.get_json()["just_registered"],
           f"status={r.status_code}")

    # Logout
    r = _post(c, "/api/auth/logout", {})
    report("logout", r.status_code == 200)
    r = c.get("/api/auth/me")
    report("me.after_logout", r.status_code == 401)

    # Login invalid
    r = _post(c, "/api/auth/login", {"voterid": "VOT123", "password": "WRONG"})
    report("login.invalid", r.status_code == 401)

    # Login valid
    r = _post(c, "/api/auth/login", {"voterid": "VOT123", "password": "secret123"})
    report("login.valid", r.status_code == 200 and r.get_json().get("success"))

    # Vote before face verified -> 403
    r = _post(c, "/api/vote", {"candidate": "BJP"})
    report("vote.unverified", r.status_code == 403,
           f"status={r.status_code}")

    # Candidates before face verified -> 403
    r = c.get("/api/candidates")
    report("candidates.unverified", r.status_code == 403,
           f"status={r.status_code}")

    # Face register
    r = _post(c, "/api/face/register", {"image": _img_b64()})
    report("face.register", r.status_code == 200 and r.get_json().get("success"))

    # Face verify
    r = _post(c, "/api/face/verify", {"image": _img_b64()})
    report("face.verify", r.status_code == 200 and r.get_json().get("success"))

    # Candidates after verify
    r = c.get("/api/candidates")
    cs = r.get_json().get("candidates", [])
    report("candidates.loaded", r.status_code == 200 and len(cs) >= 3,
           f"count={len(cs)}")

    # Vote valid
    r = _post(c, "/api/vote", {"candidate": "BJP"})
    report("vote.valid", r.status_code == 200 and r.get_json().get("success"),
           f"status={r.status_code}")

    # Duplicate vote
    r = _post(c, "/api/vote", {"candidate": "INC"})
    report("vote.duplicate", r.status_code == 409,
           f"status={r.status_code}")

    # Invalid candidate
    r = _post(c, "/api/vote", {"candidate": "NOPE"})
    report("vote.invalid_candidate", r.status_code == 404,
           f"status={r.status_code}")

    # Results
    r = c.get("/api/results")
    data = r.get_json()
    bjp = next((x for x in data["results"] if x["party"] == "BJP"), None)
    report("results.bjp_one", r.status_code == 200 and bjp and bjp["votes"] == 1,
           f"votes={bjp['votes'] if bjp else None} total={data['total_votes']}")

    # Profile
    r = c.get("/api/profile")
    data = r.get_json()
    report("profile.load", r.status_code == 200 and data["user"]["voterid"] == "VOT123"
           and data["face_exists"])

# Cleanup
shutil.rmtree(TMPDIR, ignore_errors=True)

passed = sum(1 for ok, _, _ in results if ok)
total = len(results)
print(f"\nSummary: {passed}/{total} tests passed")
if passed != total:
    sys.exit(1)