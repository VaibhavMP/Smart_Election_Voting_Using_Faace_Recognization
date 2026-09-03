# Smart Election Voting System

A face-recognition based online voting platform built with a Python Flask
backend and a modern React frontend. The project preserves the original
blue-glass visual identity while moving the user experience to a proper
single-page application that talks to a clean REST API.

> **Educational project.** This codebase is meant to demonstrate how a
> voting flow can be wired end-to-end. It is **not** suitable for real
> elections. See *Known Limitations* at the bottom of this file.

---

## Table of Contents

1. [Features](#features)
2. [Architecture](#architecture)
3. [Project Layout](#project-layout)
4. [Quick Start](#quick-start)
5. [REST API](#rest-api)
6. [Database](#database)
7. [Authentication & Sessions](#authentication--sessions)
8. [Face Verification](#face-verification)
9. [Voting Integrity](#voting-integrity)
10. [Testing](#testing)
11. [Deployment](#deployment)
12. [Configuration](#configuration)
14. [Known Limitations](#known-limitations)

---

## Features

- **Account registration** with Voter ID or Aadhaar as the login handle.
- **Profile photo capture** straight from the browser via `getUserMedia`.
- **Face verification gate** enforced server-side before voting is allowed.
- **One-person-one-vote** logic, validated inside a SQL transaction.
- **Live results** with vote counts and proportional bars.
- **Polished React UI** that keeps the original blue-gradient + glass look.
- **No Java backend, no second server.** Python handles everything from
  HTTP to image handling.

---

## Architecture

```
┌────────────────────┐
│  React (Vite) SPA  │   served on :5173 in dev, by Flask in production
│  React Router      │
│  Axios + Context   │
└──────────┬─────────┘
           │  /api/*  (withCredentials: 'include')
           ▼
┌────────────────────┐
│   Flask REST API   │   :5000 — gunicorn in production
│   (api.py)         │
└──────────┬─────────┘
           │
   ┌───────┴───────┐
   ▼               ▼
┌────────┐   ┌───────────────┐
│ SQLite │   │  OpenCV /     │
│   DB   │   │  scikit-learn │
└────────┘   └───────────────┘
```

The split is intentional. Image capture happens in the browser because that
is where the camera is. Everything that matters — identity checks, voting
rules, database writes, results — stays on the server.

---

## Project Layout

```
Smart_Election_Voting_Using_Faace_Recognization/
├── app.py                # Flask app — registers the REST blueprint
├── api.py                # /api/* endpoints (the React contract)
├── face_utils.py         # CLI/demo helpers, kept untouched
├── add_faces.py          # CLI face data collection, kept untouched
├── give_vote.py          # CLI voting helper, kept untouched
├── voting.db             # SQLite database — existing data is preserved
├── model/face_model.pkl  # Pre-trained model artifacts
├── data/                 # Existing CLI-captured face dataset
├── static/               # Hero image, logo, per-user face.png
├── templates/            # Legacy Flask templates (kept as a safety net)
├── requirments.txt       # Python deps, pinned for Python 3.11
├── Procfile / render.yaml / runtime.txt
├── smoke_test.py         # 20-case backend test suite
└── frontend/             # React + Vite single-page application
    ├── src/
    │   ├── components/   # ProtectedRoute, WebcamCapture, Alert, Spinner
    │   ├── pages/        # Splash, Home, Login, Signup, Dashboard,
    │   │                 #   FaceVerify, Vote, VoteSuccess, Results, Profile
    │   ├── context/      # AuthContext
    │   ├── services/     # Axios-backed API wrappers
    │   ├── hooks/        # useMessage
    │   ├── utils/        # format helpers
    │   ├── styles/       # global.css
    │   ├── App.jsx
    │   └── main.jsx
    ├── vite.config.js    # Proxies /api/* and /static/* to :5000 in dev
    └── package.json
```

---

## Quick Start

> Python 3.11 is the recommended interpreter. `requirments.txt` pins
> versions that do not have CPython 3.13 wheels yet.

### 1. Backend

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r .\requirments.txt
.\.venv\Scripts\python.exe app.py
```

The server starts on `http://127.0.0.1:5000`. On first launch it will create
`voting.db` if it does not exist and seed the default candidate list.

For local development, enable CORS so Vite on `:5173` can call the API
directly when needed:

```powershell
$env:ENABLE_CORS = '1'
$env:CORS_ORIGINS = 'http://127.0.0.1:5173'
python app.py
```

In production, Flask serves the React build directly, so CORS is not needed.

### 2. Frontend

```powershell
cd frontend
npm install
npm run dev
```

Open `http://localhost:5173` in your browser. Vite proxies
`/api/*` and `/static/*` to Flask on `:5000`, so the two servers
communicate as if they were one origin.

### 3. Production Build

```powershell
cd frontend
npm run build
```

The compiled assets land in `frontend/dist/`. Flask detects this folder and
mounts it at `/`, so a single gunicorn process serves both the API and the
SPA.

---

## REST API

All endpoints live under `/api/*`. The Flask session cookie is the source
of truth for authentication — React never decides who is signed in.

| Method | Endpoint               | Auth | Face | Description                                    |
| ------ | ---------------------- | ---- | ---- | ---------------------------------------------- |
| GET    | `/api/health`          | —    | —    | Liveness check                                 |
| POST   | `/api/auth/register`   | —    | —    | Create a voter account                         |
| POST   | `/api/auth/login`      | —    | —    | Login by Voter ID or Aadhaar                   |
| POST   | `/api/auth/logout`     | —    | —    | Clear session                                  |
| GET    | `/api/auth/me`         | —    | —    | Current user and session flags                 |
| POST   | `/api/face/register`   | ✅   | —    | Save profile photo for a new account           |
| POST   | `/api/face/verify`     | ✅   | —    | Verify identity before voting                  |
| GET    | `/api/profile`         | ✅   | —    | Current user info and face image existence     |
| GET    | `/api/candidates`      | ✅   | ✅   | List voting candidates                         |
| POST   | `/api/vote`            | ✅   | ✅   | Cast a vote — `{ candidate: "<party code>" }`  |
| GET    | `/api/results`         | ✅   | —    | Aggregated candidate totals                    |

### Error Contract

Errors always come back as JSON: `{ "error": "...", "message": "..." }`
alongside an HTTP status code that matches the situation.

- `400` — invalid payload
- `401` — not authenticated
- `403` — face verification required
- `404` — resource not found
- `409` — duplicate or already voted
- `500` — server error

The frontend maps these to friendly toast messages rather than dumping
stack traces on the user.

---

## Database

`voting.db` is the source of truth. Its schema is unchanged from the
original project.

| Table       | Notes                                                                              |
| ----------- | ---------------------------------------------------------------------------------- |
| `users`     | id, name, dob, gender, aadhaar (UNIQUE), voterid (UNIQUE), contact, country,       |
|             | password, face_encoding, has_voted (0/1), created_at                              |
| `votes`     | id, voter_id FK → users.id, candidate (party code), voted_at                       |
| `candidates`| id, name, party, symbol, votes                                                      |

Seeding is idempotent. Existing users, votes, and records are never
deleted or rewritten by the application.

---

## Authentication & Sessions

Sessions are Flask signed cookies. The signing key is read from the
`SECRET_KEY` environment variable and falls back to a random value during
local development. **Always set `SECRET_KEY` in any non-dev environment.**

Passwords are currently stored as **SHA-256 hashes** to remain compatible
with existing user records. SHA-256 without a salt is not an ideal choice
for password storage, so the README flags this as a known limitation and a
follow-up migration to `werkzeug.security.generate_password_hash` (scrypt)
is recommended. Rehash-on-login can be added without invalidating current
accounts.

---

## Face Verification

The browser asks for camera permission, renders a live preview, and lets
the user capture a single frame. The frame is sent as a base64 PNG to
`/api/face/register` (right after signup) or `/api/face/verify` (before
voting). The server saves the image to `static/data/<user_id>/face.png`
and flips the `face_verified` flag in the session.

Genuine biometric matching is **not** performed on the uploaded image — it
matches the behaviour of the original implementation and is documented
under *Known Limitations* below.

---

## Voting Integrity

The `/api/vote` endpoint is the only path that can record a vote, and it
enforces every rule:

1. The session must contain a `user_id`.
2. The session must contain `face_verified = True`.
3. The candidate must exist in the `candidates` table.
4. The user must not have voted before (`users.has_voted = 0`).
5. The vote insert, the `users.has_voted` flip, and the candidate
   `votes++` are wrapped in a single SQL transaction with explicit
   `BEGIN` / `COMMIT` / `ROLLBACK`.

A second vote attempt returns `409 Conflict`, even if the client bypasses
the UI entirely.

---

## Testing

The repository ships with a backend smoke test that exercises the full
flow without requiring OpenCV or scikit-learn.

```powershell
python smoke_test.py
```

Expected result:

```
[PASS] health
[PASS] register.valid
[PASS] register.duplicate_aadhaar
[PASS] register.invalid_aadhaar
[PASS] register.missing_fields
[PASS] me.after_register
[PASS] logout
[PASS] me.after_logout
[PASS] login.invalid
[PASS] login.valid
[PASS] vote.unverified
[PASS] candidates.unverified
[PASS] face.register
[PASS] face.verify
[PASS] candidates.loaded
[PASS] vote.valid
[PASS] vote.duplicate
[PASS] vote.invalid_candidate
[PASS] results.bjp_one
[PASS] profile.load

Summary: 20/20 tests passed
```

The frontend ships with a clean `npm run build` (no warnings apart from the
expected runtime-resolved static asset paths).

---

## Deployment

The repository already targets Python 3.11 through `runtime.txt` and
`render.yaml`. The recommended production layout:

1. `npm run build` produces `frontend/dist/`.
2. Flask starts and detects the build output, mounting it at `/`.
3. Gunicorn serves the combined API + SPA on a single port.

`render.yaml`:

```yaml
buildCommand: pip install -r requirments.txt && npm --prefix frontend ci && npm --prefix frontend run build
startCommand: gunicorn app:app --workers 2 --bind 0.0.0.0:$PORT
runtime: python
envVars:
  PYTHON_VERSION: 3.11.0
  FLASK_DEBUG: false
  ENABLE_CORS: ""
  SECRET_KEY: <generated>
```

For other platforms (Heroku, Fly, a plain VPS), the same shape applies:
build the frontend, then run gunicorn.

---

## Configuration

| Variable        | Purpose                                                            |
| --------------- | ------------------------------------------------------------------ |
| `SECRET_KEY`    | Flask session signing key. Set in any non-dev environment.         |
| `PORT`          | HTTP port. Defaults to `5000`.                                     |
| `FLASK_DEBUG`   | Set to `true` for development reloads. Never enable in production. |
| `ENABLE_CORS`   | `1` enables narrow CORS for local cross-origin dev.                |
| `CORS_ORIGINS`  | Allowed origin for CORS (default: `http://127.0.0.1:5173`).        |
| `FACE_IMAGE_DIR`| Override the face-image storage path (used by tests).              |

---

## Known Limitations

- **Password hashing.** SHA-256 without a salt is preserved for backward
  compatibility with the existing `voting.db`. A migration to scrypt via
  `werkzeug.security` with rehash-on-login is the recommended upgrade.
- **Biometric matching.** The web face flow captures and stores the photo
  and flips a session flag. It does **not** run face-matching on the
  uploaded image; that matches the original project's behaviour. Wiring
  the existing OpenCV/scikit-learn model into the request handler is a
  separate enhancement.
- **CSRF.** Safe under same-origin in production. Cross-origin
  deployments need an explicit CSRF strategy.
- **SQLite.** Perfectly fine for a demo, not appropriate for a real
  election. A hardened PostgreSQL deployment with proper audit trails is
  required for any non-educational use.
- **Not a real election system.** Treat this codebase as a learning
  artifact. Real elections demand substantial additional work around
  security, privacy, accessibility, identity verification, and
  regulatory compliance.