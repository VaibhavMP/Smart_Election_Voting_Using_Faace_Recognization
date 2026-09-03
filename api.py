"""
Flask REST API Blueprint for the Smart Election Voting System.

This module exposes JSON endpoints under /api/* that the React frontend
consumes. All business logic is delegated to helpers in ``app.py`` and the
existing SQLite schema is reused unchanged.

The blueprint is intentionally additive: existing template-based routes
remain functional during the migration.
"""

from __future__ import annotations

import base64
import os
import re
import sqlite3
from functools import wraps

from flask import Blueprint, current_app, jsonify, request, session

api_bp = Blueprint("api", __name__, url_prefix="/api")


# ---------------------------------------------------------------------------
# Helpers / decorators
# ---------------------------------------------------------------------------


def _json_error(status_code: int, message: str, **extra):
    payload = {"error": message, "message": message}
    payload.update(extra)
    return jsonify(payload), status_code


def _db():
    """Open a SQLite connection using the application's DB_PATH."""
    from app import DB_PATH, get_db_connection

    # Re-use the app's helper so row_factory stays consistent.
    return get_db_connection()


def _hash_password(password: str) -> str:
    """SHA-256 hashing kept for backward compatibility with existing users."""
    from app import hash_password

    return hash_password(password)


def _require_json():
    if not request.is_json:
        return _json_error(400, "Request must be JSON")
    return None


def _require_auth(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        if "user_id" not in session:
            return _json_error(401, "Authentication required")
        return fn(*args, **kwargs)

    return wrapper


def _require_face_verified(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        if "user_id" not in session:
            return _json_error(401, "Authentication required")
        if not session.get("face_verified", False):
            return _json_error(
                403, "Face verification required before this action"
            )
        return fn(*args, **kwargs)

    return wrapper


def _decode_image(image_data: str):
    """Decode a base64 (data URL or raw) image payload."""
    if not image_data:
        raise ValueError("No image provided")
    if "base64," in image_data:
        image_data = image_data.split("base64,", 1)[1]
    return base64.b64decode(image_data)


def _save_face_image(user_id: int, raw_bytes: bytes) -> str:
    """Persist the captured image to <face_dir>/<user_id>/face.png.

    ``face_dir`` can be overridden via the ``FACE_IMAGE_DIR`` env var so
    tests can use a temp directory and never write into the real
    ``static/data`` folder.
    """
    face_dir = os.environ.get("FACE_IMAGE_DIR", os.path.join("static", "data"))
    user_folder = os.path.join(face_dir, str(user_id))
    os.makedirs(user_folder, exist_ok=True)
    face_file = os.path.join(user_folder, "face.png")
    with open(face_file, "wb") as f:
        f.write(raw_bytes)
    return face_file


# ---------------------------------------------------------------------------
# Health
# ---------------------------------------------------------------------------


@api_bp.get("/health")
def health():
    return jsonify({"status": "ok"})


# ---------------------------------------------------------------------------
# Authentication
# ---------------------------------------------------------------------------


_EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


@api_bp.post("/auth/register")
def register():
    err = _require_json()
    if err:
        return err
    data = request.get_json(silent=True) or {}

    required = [
        "name",
        "dob",
        "gender",
        "aadhaar",
        "voterid",
        "mobile",
        "email",
        "address",
        "country",
        "password",
    ]
    missing = [k for k in required if not str(data.get(k, "")).strip()]
    if missing:
        return _json_error(400, f"Missing fields: {', '.join(missing)}")

    aadhaar = str(data["aadhaar"]).strip()
    if len(aadhaar) != 12 or not aadhaar.isdigit():
        return _json_error(400, "Aadhaar must be 12 digits")

    mobile = str(data["mobile"]).strip()
    if len(mobile) != 10 or not mobile.isdigit():
        return _json_error(400, "Mobile must be 10 digits")

    email = str(data["email"]).strip()
    if not _EMAIL_RE.match(email):
        return _json_error(400, "Invalid email address")

    password = str(data["password"])
    if len(password) < 6:
        return _json_error(400, "Password must be at least 6 characters")

    hashed = _hash_password(password)

    conn = _db()
    try:
        cur = conn.cursor()
        cur.execute(
            """
            INSERT INTO users (
                name, dob, gender, aadhaar, voterid, mobile, email,
                address, country, password
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                data["name"].strip(),
                data["dob"].strip(),
                data["gender"].strip(),
                aadhaar,
                str(data["voterid"]).strip(),
                mobile,
                email,
                data["address"].strip(),
                data["country"].strip(),
                hashed,
            ),
        )
        user_id = cur.lastrowid
        conn.commit()
    except sqlite3.IntegrityError:
        conn.close()
        return _json_error(409, "Aadhaar or Voter ID already registered")
    except sqlite3.Error as e:
        conn.close()
        return _json_error(500, f"Database error: {e}")
    finally:
        try:
            conn.close()
        except Exception:
            pass

    session["user_id"] = user_id
    session["user_name"] = data["name"].strip()
    session["just_registered"] = True

    return jsonify(
        {
            "success": True,
            "user": {"id": user_id, "name": session["user_name"]},
            "just_registered": True,
            "face_verified": False,
        }
    )


@api_bp.post("/auth/login")
def login():
    err = _require_json()
    if err:
        return err
    data = request.get_json(silent=True) or {}

    voterid = str(data.get("voterid", "")).strip()
    password = str(data.get("password", ""))
    if not voterid or not password:
        return _json_error(400, "Voter ID/Aadhaar and password are required")

    hashed = _hash_password(password)

    conn = _db()
    try:
        cur = conn.cursor()
        cur.execute(
            """
            SELECT id, name, voterid, aadhaar FROM users
            WHERE (voterid = ? OR aadhaar = ?) AND password = ?
            """,
            (voterid, voterid, hashed),
        )
        user = cur.fetchone()
    finally:
        conn.close()

    if not user:
        return _json_error(401, "Invalid Voter ID/Aadhaar or Password")

    session["user_id"] = user["id"]
    session["user_name"] = user["name"]
    session["voterid"] = user["voterid"]
    session.pop("just_registered", None)
    session.pop("face_verified", None)

    return jsonify(
        {
            "success": True,
            "user": {
                "id": user["id"],
                "name": user["name"],
                "voterid": user["voterid"],
            },
            "face_verified": False,
            "just_registered": False,
        }
    )


@api_bp.post("/auth/logout")
def logout():
    session.clear()
    return jsonify({"success": True})


@api_bp.get("/auth/me")
def me():
    if "user_id" not in session:
        return _json_error(401, "Not authenticated")

    conn = _db()
    try:
        cur = conn.cursor()
        cur.execute(
            "SELECT id, name, voterid, has_voted FROM users WHERE id = ?",
            (session["user_id"],),
        )
        user = cur.fetchone()
    finally:
        conn.close()

    if not user:
        session.clear()
        return _json_error(404, "User not found")

    return jsonify(
        {
            "user": {
                "id": user["id"],
                "name": user["name"],
                "voterid": user["voterid"],
                "has_voted": user["has_voted"],
            },
            "face_verified": bool(session.get("face_verified", False)),
            "just_registered": bool(session.get("just_registered", False)),
        }
    )


# ---------------------------------------------------------------------------
# Face registration / verification
# ---------------------------------------------------------------------------


@api_bp.post("/face/register")
@_require_auth
def face_register():
    err = _require_json()
    if err:
        return err
    data = request.get_json(silent=True) or {}

    try:
        raw = _decode_image(data.get("image", ""))
    except ValueError as e:
        return _json_error(400, str(e))
    except Exception as e:
        return _json_error(400, f"Invalid image data: {e}")

    user_id = session["user_id"]
    try:
        _save_face_image(user_id, raw)
    except OSError as e:
        return _json_error(500, f"Failed to save image: {e}")

    session["face_verified"] = True
    session["face_captured"] = True
    session.pop("just_registered", None)

    return jsonify({"success": True, "message": "Profile photo saved"})


@api_bp.post("/face/verify")
@_require_auth
def face_verify():
    err = _require_json()
    if err:
        return err
    data = request.get_json(silent=True) or {}

    try:
        raw = _decode_image(data.get("image", ""))
    except ValueError as e:
        return _json_error(400, str(e))
    except Exception as e:
        return _json_error(400, f"Invalid image data: {e}")

    user_id = session["user_id"]

    # Existing behaviour: save the captured image and flag the user as verified.
    # Genuine biometric matching would happen here. See README "Security notes".
    try:
        _save_face_image(user_id, raw)
    except OSError as e:
        return _json_error(500, f"Failed to save image: {e}")

    session["face_verified"] = True
    session["face_captured"] = True

    return jsonify({"success": True, "message": "Face verified"})


# ---------------------------------------------------------------------------
# Profile
# ---------------------------------------------------------------------------


@api_bp.get("/profile")
@_require_auth
def profile():
    user_id = session["user_id"]
    conn = _db()
    try:
        cur = conn.cursor()
        cur.execute(
            """
            SELECT id, name, aadhaar, voterid, email, mobile, address,
                   dob, gender, country, has_voted
            FROM users WHERE id = ?
            """,
            (user_id,),
        )
        user = cur.fetchone()
    finally:
        conn.close()

    if not user:
        return _json_error(404, "User not found")

    face_path = os.path.join("static", "data", str(user_id), "face.png")
    face_exists = os.path.exists(face_path)

    return jsonify(
        {
            "user_id": user_id,
            "user": {
                "id": user["id"],
                "name": user["name"],
                "aadhaar": user["aadhaar"],
                "voterid": user["voterid"],
                "email": user["email"],
                "mobile": user["mobile"],
                "address": user["address"],
                "dob": user["dob"],
                "gender": user["gender"],
                "country": user["country"],
                "has_voted": user["has_voted"],
            },
            "face_exists": face_exists,
        }
    )


# ---------------------------------------------------------------------------
# Candidates / Voting / Results
# ---------------------------------------------------------------------------


@api_bp.get("/candidates")
@_require_face_verified
def candidates():
    conn = _db()
    try:
        cur = conn.cursor()
        cur.execute("SELECT id, name, party, symbol FROM candidates ORDER BY id")
        rows = cur.fetchall()
    finally:
        conn.close()

    return jsonify(
        {
            "candidates": [
                {"id": r["id"], "name": r["name"], "party": r["party"], "symbol": r["symbol"]}
                for r in rows
            ]
        }
    )


@api_bp.post("/vote")
@_require_face_verified
def cast_vote():
    err = _require_json()
    if err:
        return err
    data = request.get_json(silent=True) or {}
    candidate_party = (data.get("candidate") or "").strip()
    if not candidate_party:
        return _json_error(400, "Candidate is required")

    user_id = session["user_id"]
    conn = _db()
    try:
        cur = conn.cursor()

        cur.execute(
            "SELECT id, party FROM candidates WHERE party = ?", (candidate_party,)
        )
        candidate = cur.fetchone()
        if not candidate:
            conn.close()
            return _json_error(404, "Candidate not found")

        cur.execute("SELECT has_voted FROM users WHERE id = ?", (user_id,))
        user = cur.fetchone()
        if not user:
            conn.close()
            session.clear()
            return _json_error(401, "User not found")
        if user["has_voted"] == 1:
            conn.close()
            return _json_error(409, "You have already voted")

        try:
            cur.execute("BEGIN")
            cur.execute(
                "INSERT INTO votes (voter_id, candidate) VALUES (?, ?)",
                (user_id, candidate_party),
            )
            cur.execute(
                "UPDATE users SET has_voted = 1 WHERE id = ?", (user_id,)
            )
            cur.execute(
                "UPDATE candidates SET votes = votes + 1 WHERE party = ?",
                (candidate_party,),
            )
            cur.execute("COMMIT")
        except sqlite3.Error:
            cur.execute("ROLLBACK")
            conn.close()
            return _json_error(500, "Failed to record vote")

        cur.execute("SELECT name, party FROM candidates WHERE id = ?", (candidate["id"],))
        full = cur.fetchone()
        conn.close()

        session["last_voted_party"] = candidate_party

        return jsonify(
            {
                "success": True,
                "candidate": candidate_party,
                "candidate_name": full["name"] if full else candidate_party,
            }
        )
    except sqlite3.Error as e:
        try:
            conn.close()
        except Exception:
            pass
        return _json_error(500, f"Database error: {e}")


@api_bp.get("/results")
@_require_auth
def results():
    conn = _db()
    try:
        cur = conn.cursor()
        cur.execute(
            "SELECT id, name, party, symbol, votes FROM candidates ORDER BY votes DESC"
        )
        rows = cur.fetchall()
    finally:
        conn.close()

    total = sum(r["votes"] for r in rows)
    return jsonify(
        {
            "results": [
                {
                    "id": r["id"],
                    "name": r["name"],
                    "party": r["party"],
                    "symbol": r["symbol"],
                    "votes": r["votes"],
                }
                for r in rows
            ],
            "total_votes": total,
        }
    )