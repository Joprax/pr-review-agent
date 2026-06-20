# PR Review Agent

An AI-powered Pull Request reviewer that automatically analyzes code changes, identifies bugs and security vulnerabilities, and posts structured feedback directly on GitHub PRs within seconds of opening them.

---

## Overview

PR Review Agent integrates with GitHub via webhooks and runs a multi-stage analysis pipeline on every pull request diff. Reviews are processed asynchronously using a task queue, stored in a relational database, and surfaced through a web dashboard.

The project demonstrates a production-grade AI automation architecture: event-driven ingestion, background task processing, structured AI output parsing, third-party API integration, and a full-stack deployment across two cloud platforms.

---

## Demo

![Demo](docs/demo.gif)

Live dashboard: `https://pr-review-agent-dashboard-93t9k8p8l-joprax-s-projects.vercel.app`

---

## Features

- Webhook listener that receives GitHub PR events and responds within GitHub's 10-second timeout
- Asynchronous AI analysis via Celery and Redis — processing continues in the background after the webhook returns
- Code diff analysis using Google Gemini 2.5 Flash, returning findings structured by file, line, severity, and suggested fix
- Automatic inline comment posted to the GitHub PR on completion
- PostgreSQL persistence for all reviews and findings
- REST API exposing review history and statistics
- Next.js dashboard showing reviewed PRs, severity breakdowns, and per-PR finding details

---

## Architecture

```
GitHub PR opened
       |
       v
FastAPI webhook receiver
       |
       +-- responds 200 OK immediately
       |
       v
Redis task queue
       |
       v
Celery worker
       |
       +-- fetches PR diff via GitHub API
       |
       +-- sends diff to Gemini 2.5 Flash
       |
       +-- parses structured findings
       |
       +-- posts comment to GitHub PR
       |
       v
PostgreSQL (review persisted)
       |
       v
Next.js dashboard (Vercel)
```

---

## Tech Stack

| Layer | Technology |
|---|---|
| Backend framework | FastAPI |
| AI model | Google Gemini 2.5 Flash |
| Task queue | Celery |
| Message broker | Redis |
| Database | PostgreSQL with SQLAlchemy ORM |
| Frontend | Next.js, TypeScript, Tailwind CSS |
| Backend hosting | Railway |
| Frontend hosting | Vercel |
| GitHub integration | Webhooks, REST API v3 |

---

## Project Structure

```
pr-review-agent/
├── backend/
│   ├── main.py          # FastAPI application — webhook receiver and data API
│   ├── worker.py        # Celery task definitions — AI review pipeline
│   ├── models.py        # SQLAlchemy ORM models
│   └── init_db.py       # Database table initialization
├── frontend/
│   └── app/
│       └── page.tsx     # Next.js dashboard
├── docker-compose.yml   # Local PostgreSQL and Redis
├── Dockerfile           # Container configuration for Railway deployment
├── Procfile             # Process definitions for Railway
├── requirements.txt     # Python dependencies
└── .env.example         # Environment variable template
```

---

## Getting Started

### Prerequisites

- Python 3.10 or higher
- Node.js 18 or higher
- Docker Desktop
- Google AI Studio account — [aistudio.google.com](https://aistudio.google.com)
- GitHub account

### Installation

**1. Clone the repository**

```bash
git clone https://github.com/Joprax/pr-review-agent.git
cd pr-review-agent
```

**2. Set up Python environment**

```bash
python -m venv venv
venv\Scripts\activate        # Windows
source venv/bin/activate     # Mac/Linux

pip install -r requirements.txt
```

**3. Configure environment variables**

```bash
cp .env.example .env
```

Edit `.env` with your credentials:

```
GEMINI_API_KEY=your_gemini_api_key
GITHUB_TOKEN=your_github_classic_token
GITHUB_WEBHOOK_SECRET=any_random_string
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/pr_agent
REDIS_URL=redis://localhost:6379/0
```

Obtaining credentials:
- `GEMINI_API_KEY` — [aistudio.google.com](https://aistudio.google.com) → Get API key → Create API key in new project
- `GITHUB_TOKEN` — GitHub → Settings → Developer Settings → Personal Access Tokens → Tokens (classic) → Generate new token → select `repo` scope only

**4. Start local services**

```bash
docker-compose up -d
```

**5. Initialize the database**

```bash
python -m backend.init_db
```

**6. Start the application**

Run each command in a separate terminal:

```bash
# Terminal 1 — API server
uvicorn backend.main:app --reload --port 8000

# Terminal 2 — background worker
celery -A backend.worker.celery_app worker --loglevel=info --pool=solo

# Terminal 3 — public tunnel for local webhook testing
ngrok http 8000
```

**7. Configure the GitHub webhook**

1. Go to any GitHub repository → Settings → Webhooks → Add webhook
2. Set Payload URL to: `https://your-ngrok-url/webhooks/github`
3. Set Content type to: `application/json`
4. Under events, select: Pull requests
5. Click Add webhook

**8. Start the dashboard**

```bash
cd frontend
cp .env.local.example .env.local
# set NEXT_PUBLIC_API_URL=http://localhost:8000
npm install
npm run dev
```

Open `http://localhost:3000`

### Testing

Open a pull request on your connected repository. The agent will:

1. Receive the webhook event
2. Fetch the code diff
3. Send it to Gemini for analysis
4. Post a structured review comment on the PR
5. Save the findings to the database
6. Display the review in the dashboard

---

## API Reference

| Method | Endpoint | Description |
|---|---|---|
| POST | `/webhooks/github` | Receives GitHub PR webhook events |
| GET | `/health` | Health check |
| GET | `/api/stats` | Summary counts — PRs reviewed, findings by severity |
| GET | `/api/reviews` | All reviewed PRs with finding counts |
| GET | `/api/reviews/{id}/findings` | Detailed findings for a specific PR |

---

## Using the Live Instance

You can connect the hosted instance to any repository without deploying your own:

1. Go to your repository → Settings → Webhooks → Add webhook
2. Set Payload URL to:
```
https://pr-review-agent-production-377c.up.railway.app/webhooks/github
```
3. Set Content type to: `application/json`
4. Select Pull requests under events
5. Save

Every PR opened in that repository will be reviewed automatically.

Note: the live instance uses a free-tier AI quota. Reviews may occasionally fail during high-usage periods. For guaranteed uptime, deploy your own instance.

---

## Deployment

The backend is designed for Railway deployment. The `Dockerfile` and `Procfile` in the project root define the web and worker processes. Set the same environment variables as your local `.env` in Railway's variable settings, using Railway's internal `DATABASE_URL` and `REDIS_URL` from the managed database services.

The frontend deploys to Vercel. Set `NEXT_PUBLIC_API_URL` to your Railway backend URL in Vercel's environment variable settings.

---

## Roadmap

- Webhook signature verification using HMAC-SHA256
- Re-review trigger when new commits are pushed to an open PR
- Slack notifications for critical severity findings
- Per-repository configuration for custom rules and severity thresholds
- Support for re-running reviews on demand via dashboard

---

## License

MIT

---

## Author

Joprax — Computer Engineering, Cebu Institute of Technology University
GitHub: [Joprax](https://github.com/Joprax)