# 🤖 PR Review Agent

An AI-powered Pull Request reviewer that automatically analyzes code changes, detects bugs and security issues, and posts structured feedback directly on your GitHub PRs — within seconds of opening them.

Built with FastAPI, Gemini 2.5 Flash, Celery, PostgreSQL, and Next.js. Fully deployed on Railway and Vercel.

---

![Demo](docs/demo.gif)
> *AI review comment posted automatically on a GitHub PR within seconds of opening it*

---

## ✨ Features

- **Automatic code review** — triggered the moment a PR is opened, no manual action needed
- **AI-powered analysis** — detects bugs, security vulnerabilities, and code quality issues
- **Structured feedback** — every finding includes file name, line number, severity, and a fix suggestion
- **Inline PR comments** — results posted directly on GitHub as a formatted comment
- **Async processing** — responds to GitHub instantly, processes AI review in the background
- **Persistent history** — every review saved to PostgreSQL
- **Live dashboard** — view all reviewed PRs, findings, and severity breakdowns at a glance

---

## 🏗️ Architecture

```
Developer opens PR on GitHub
          ↓
GitHub Webhook (POST /webhooks/github)
          ↓
FastAPI — responds 200 OK instantly
          ↓
Redis → Celery Worker (background)
          ↓                    ↓
    GitHub API            Gemini 2.5 Flash
    (fetch diff)          (AI code review)
          ↓
    PR Comment posted on GitHub automatically
          ↓
    PostgreSQL — review saved
          ↓
    Next.js Dashboard — visible at your Vercel URL
```

---

## 🚀 Live Demo

| Service | URL |
|---|---|
| Dashboard | [pr-review-agent-dashboard.vercel.app](https://pr-review-agent-dashboard-93t9k8p8l-joprax-s-projects.vercel.app) |
| Backend API | [pr-review-agent.railway.app/health](https://pr-review-agent-production-377c.up.railway.app/health) |

### Try it instantly — add this webhook to any GitHub repo:

```
https://pr-review-agent-production-377c.up.railway.app/webhooks/github
```

Go to your repo → **Settings → Webhooks → Add webhook** → paste the URL above → set content type to `application/json` → select **Pull requests** event → save. Open a PR and watch the AI review appear automatically.

---

## 🛠️ Tech Stack

| Layer | Technology |
|---|---|
| Backend API | FastAPI + Python 3.11 |
| AI Model | Google Gemini 2.5 Flash |
| Task Queue | Celery + Redis |
| Database | PostgreSQL + SQLAlchemy |
| Frontend | Next.js + TypeScript + Tailwind CSS |
| Backend hosting | Railway |
| Frontend hosting | Vercel |
| GitHub integration | GitHub Webhooks + REST API |

---

## 📦 Self-hosting guide

Follow these steps to run your own instance.

### Prerequisites

- Python 3.10+
- Node.js 18+
- Docker Desktop
- A Google AI Studio account (free) — [aistudio.google.com](https://aistudio.google.com)
- A GitHub account

### 1. Clone the repo

```bash
git clone https://github.com/Joprax/pr-review-agent.git
cd pr-review-agent
```

### 2. Set up Python environment

```bash
python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # Mac/Linux

pip install -r requirements.txt
```

### 3. Configure environment variables

```bash
cp .env.example .env
```

Open `.env` and fill in your values:

```
GEMINI_API_KEY=your_gemini_api_key_here
GITHUB_TOKEN=your_github_classic_token_here
GITHUB_WEBHOOK_SECRET=make_up_any_random_string
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/pr_agent
REDIS_URL=redis://localhost:6379/0
```

**Getting your keys:**
- `GEMINI_API_KEY` — go to [aistudio.google.com](https://aistudio.google.com) → Get API key → Create API key
- `GITHUB_TOKEN` — go to GitHub → Settings → Developer Settings → Personal Access Tokens → Tokens (classic) → Generate new token → check `repo` scope only

### 4. Start the database and Redis

```bash
docker-compose up -d
```

### 5. Create database tables

```bash
python -m backend.init_db
```

### 6. Start the backend

Open three terminals:

```bash
# Terminal 1 — FastAPI server
uvicorn backend.main:app --reload --port 8000

# Terminal 2 — Celery worker
celery -A backend.worker.celery_app worker --loglevel=info --pool=solo

# Terminal 3 — ngrok (for local webhook testing)
ngrok http 8000
```

### 7. Connect a GitHub repo

1. Copy your ngrok URL (e.g. `https://abc123.ngrok-free.app`)
2. Go to any GitHub repo → **Settings → Webhooks → Add webhook**
3. Set Payload URL to: `https://your-ngrok-url/webhooks/github`
4. Set Content type to: `application/json`
5. Select **Pull requests** under events
6. Click **Add webhook**

### 8. Start the dashboard

```bash
cd frontend
cp .env.local.example .env.local
# set NEXT_PUBLIC_API_URL=http://localhost:8000
npm install
npm run dev
```

Open [http://localhost:3000](http://localhost:3000)

### 9. Test it

Open a Pull Request on your connected repo. Within 30–60 seconds you should see:
- An AI review comment posted on the PR automatically
- The review appearing in your dashboard at localhost:3000

---

## 📁 Project structure

```
pr-review-agent/
├── backend/
│   ├── main.py        ← FastAPI app — webhook receiver + data API
│   ├── worker.py      ← Celery tasks — AI review pipeline
│   ├── models.py      ← SQLAlchemy database models
│   └── init_db.py     ← Creates database tables
├── frontend/
│   └── app/
│       └── page.tsx   ← Next.js dashboard
├── docker-compose.yml ← Local PostgreSQL + Redis
├── Dockerfile         ← Container config for Railway
├── Procfile           ← Process definitions for Railway
├── requirements.txt   ← Python dependencies
└── .env.example       ← Environment variable template
```

---

## 🔍 What the AI catches

The agent reviews every PR diff and flags issues including:

- **Critical** — SQL injection, hardcoded secrets, API keys in source code
- **Major** — division by zero, off-by-one errors, missing null checks, unhandled exceptions
- **Minor** — code style, redundant logic, non-Pythonic patterns

Each finding includes the exact file, line number, a description of the issue, and a concrete suggestion for how to fix it.

---

## 🗺️ Roadmap

- [ ] Webhook signature verification (HMAC-SHA256)
- [ ] Re-review on new commits pushed to an open PR
- [ ] Slack notifications for critical findings
- [ ] Per-repo configuration (custom rules, severity thresholds)
- [ ] Support for more languages (currently best with Python, JS, TS)

---

## 👤 Author

**Kelly** — Computer Engineering graduate, Cebu Institute of Technology – University
- GitHub: [@Joprax](https://github.com/Joprax)

---

## 📄 License

MIT — free to use, modify, and deploy.
