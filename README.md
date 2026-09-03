# Smart Election Voting System 🔗

A face-recognition based online voting application — **Python Flask backend + React (Vite) frontend**.

> This is an educational/demo project. It is **not** suitable for real-world
> elections. See *Known Limitations* at the end of this document.

---

## 🌟 Features

- **Signup / Login** — Voter ID **or** Aadhaar + password (Flask session-based auth)
- **Profile Photo Capture** — webcam capture via `getUserMedia`
- **Face Verification** — server-side gate before voting
- **Voting** — candidate selection with server-enforced *one person, one vote*
- **Results** — aggregated from SQLite, sorted by votes
- **Profile** — view your details and registered profile photo
- **Modern UI** — React + Vite, preserving the project's blue-gradient / glassmorphism aesthetic

---

## 🏛️ Architecture

```
┌────────────────────┐
│  React (Vite) SPA  │  ← http://localhost:5173 (dev)   │
│  React Router      │     served by Flask in prod     │
│  Axios + Context   │                                  │
└──────────┬─────────┘                                  │
           │  /api/*  (withCredentials: 'include')    │
           ▼                                           │
┌────────────────────┐                                  │
│   Flask REST API   │  ← http://localhost:5000         │
│   (api.py)         │                                  │
└──────────┬─────────┘                                  │
           │                                           │
   ┌───────┴───────┐                                   │
   ▼               ▼                                   │
┌────────┐   ┌───────────────┐                         │
│ SQLite │   │  OpenCV /     │                         │
│   DB   │   │  scikit-learn │                         │
└────────┘   └───────────────┘                         │
```

- **The backend is 100% Python** (Flask + SQLite + OpenCV + scikit-learn + NumPy + Pillow).
- **The only Node.js portion is the React frontend + Vite tooling.**
- Face recognition / image processing stays in Python. React only opens the webcam
  and uploads a base64 PNG to Flask.

---

## 📁 Project Structure

```
Smart_Election_Voting_Using_Faace_Recognization/
├── app.py                # Flask app — registers the REST blueprint
├── api.py                # /api/* REST endpoints (the React contract)
├── face_utils.py         # CLI/demo helpers (kept untouched)
├── add_faces.py          # CLI face data collection (kept untouched)
├── give_vote.py          # CLI voting helper (kept untouched)
├── voting.db             # SQLite database (existing — preserved)
├── model/face_model.pkl  # Pre-trained model artifacts (kept untouched)
├── data/                 # Existing CLI-captured face dataset
├── static/               # Images + per-user face.png
│   ├── images/           # Hero + logo (referenced by React)
│   └── data/<user_id>/   # Captured profile photos (per user)
├── templates/            # Legacy Flask templates (kept for fallback / parity)
├── requirments.txt       # Python deps (Python 3.11 target)
├── Procfile / render.yaml / runtime.txt
├── frontend/             # NEW: React + Vite SPA
│   ├── src/
│   │   ├── components/   # ProtectedRoute, WebcamCapture, Alert, Spinner
│   │   ├── pages/        # Splash, Home, Login, Signup, Dashboard,
│   │   │                 #   FaceVerify, Vote, VoteSuccess, Results, Profile
│   │   ├── context/      # AuthContext
│   │   ├── services/     # Axios-backed API wrappers
│   │   ├── hooks/        # useMessage
│   │   ├── utils/        # formatting helpers
│   │   ├── styles/       # global.css (preserves original design)
│   │   ├── App.jsx
│   │   └── main.jsx
│   ├── vite.config.js    # /api + /static proxy to :5000 in dev
│   └── package.json
└── smoke_test.py         # 20-case backend test suite (no OpenCV needed)
```

---

## 🚀 Local Setup

> Python 3.11 is recommended — `requirments.txt` pins versions that don't
> have CPython 3.13 wheels yet.

### Backend (Python 3.11)

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r .\requirments.txt
.\.venv\Scripts\python.exe app.py
# → http://127.0.0.1:5000
```

The first start will:
- create `voting.db` if missing,
- seed default candidates,
- register `/api/*` routes alongside the legacy templates.

### Frontend (Node 18+)

```powershell
cd frontend
npm install
npm run dev
# → http://127.0.0.1:5173  (proxies /api/* and /static/* → :5000)
```

Open the React app at **http://127.0.0.1:5173**.

### Production build

```powershell
cd frontend
npm run build          # produces frontend/dist/
```

For a same-origin deployment, point Flask at the build output:

```python
# (handled by app.py when frontend/dist/index.html exists)
```

---

## 🔌 REST API

All endpoints live under `/api/*`. The Flask session cookie (`session`) is
authoritative — React **never** decides who is authenticated.

| Method | Endpoint               | Auth | Face | Description                                  |
| ------ | ---------------------- | ---- | ---- | -------------------------------------------- |
| GET    | `/api/health`          | —    | —    | Service health check                         |
| POST   | `/api/auth/register`   | —    | —    | Create voter account, marks `just_registered`|
| POST   | `/api/auth/login`      | —    | —    | Login by Voter ID **or** Aadhaar             |
| POST   | `/api/auth/logout`     | —    | —    | Clear session                                |
| GET    | `/api/auth/me`         | —    | —    | Returns current user + session flags         |
| POST   | `/api/face/register`   | ✅   | —    | Save profile photo for newly registered user |
| POST   | `/api/face/verify`     | ✅   | —    | Verify identity before voting                |
| GET    | `/api/profile`         | ✅   | —    | Current user info + face image existence     |
| GET    | `/api/candidates`      | ✅   | ✅   | List voting candidates                       |
| POST   | `/api/vote`            | ✅   | ✅   | Cast vote (`{ candidate: "<party code>" }`)  |
| GET    | `/api/results`         | ✅   | —    | Aggregated candidate totals                  |

### Error contract

All errors return JSON: `{ "error": "...", "message": "..." }` plus appropriate HTTP code:

- `400` — invalid payload
- `401` — not authenticated
- `403` — face verification required
- `404` — resource not found
- `409` — duplicate / already voted
- `500` — server error

---

## 🗄️ Database

`voting.db` is **authoritative** — its schema is unchanged:

| Table       | Notes                                                                  |
| ----------- | ---------------------------------------------------------------------- |
| `users`     | id, name, dob, gender, aadhaar (UNIQUE), voterid (UNIQUE), contact,    |
|             | country, password, face_encoding, has_voted (0/1), created_at          |
| `votes`     | id, voter_id FK → users.id, candidate (party code), voted_at          |
| `candidates`| id, name, party (UNIQUE key in practice), symbol, votes                |

Existing users are **never** deleted or migrated. Candidate seeding is idempotent.

---

## 🔐 Security Notes

- **Sessions** — Flask's signed cookie session. `SECRET_KEY` should be set via env var in any non-dev environment.
- **Passwords** — currently **SHA-256 (no salt)** to preserve backward
  compatibility with existing users. *This is not ideal for password storage.*
  A migration to `werkzeug.security.generate_password_hash` (scrypt / pbkdf2)
  is a deliberate follow-up — see *Known Limitations*.
- **CSRF** — the REST API uses session cookies + same-origin policy in
  production. For cross-origin deployments, an explicit CSRF strategy is required.
- **One vote** — enforced server-side: the `/api/vote` handler checks
  `users.has_voted` inside a SQL transaction, so duplicate votes return `409`
  even if the client bypasses the UI.
- **Face verification** — captures and stores a profile image; the
  `face_verified` flag is set only after a successful `POST /api/face/verify`.
  Genuine biometric matching is **not** currently performed on the request
  payload (this matches the legacy behaviour).
- **CORS** — narrow, opt-in via `ENABLE_CORS=1` env var. In production the
  React build is served by Flask, so CORS is not needed.

---

## 🧪 Testing

```powershell
# Backend smoke tests (no OpenCV / sklearn required)
python smoke_test.py
# → 20/20 should pass

# React production build
cd frontend && npm run build
```

Manual end-to-end:

```
Splash → Home → Signup → Face registration → Login
     → Dashboard → Face verification → Vote
     → (second Vote attempt is blocked) → Results → Profile → Logout
```

---

## 🚢 Deployment (Render)

`render.yaml`, `Procfile`, and `runtime.txt` already target **Python 3.11**.

The recommended production layout is:

```
React production build (frontend/dist)
        ↓ copied / served by
Python Flask app (gunicorn)
        ↓
SQLite (voting.db persisted to disk)
```

For Render:

1. `buildCommand`: `pip install -r requirments.txt && npm --prefix frontend ci && npm --prefix frontend run build`
2. `startCommand`: `gunicorn app:app --workers 2 --bind 0.0.0.0:$PORT`
3. Flask serves `/static/*` (existing), and when `frontend/dist/index.html`
   is present it is also mounted at `/` so React handles routing client-side.

---

## 📜 Known Limitations

- **SHA-256 password hashing** is preserved for backward compatibility with
  existing users. Production deployments should migrate to
  `werkzeug.security.generate_password_hash` (scrypt) with a rehash-on-login
  strategy.
- **Face verification** does not currently perform biometric matching on the
  uploaded image — it stores the photo and sets a session flag (mirrors the
  legacy behaviour). Wiring the existing OpenCV/scikit-learn model into the
  request flow is a separate enhancement.
- **SQLite** is fine for an educational project but does not support
  concurrent writers or replication. A production election platform requires
  PostgreSQL or similar with a hardened audit trail.
- **No CSRF tokens** are issued — safe under same-origin in production but
  not under cross-origin.
- **Educational only** — this code must not be used for real elections
  without substantial additional security, privacy, accessibility, and
  regulatory controls.