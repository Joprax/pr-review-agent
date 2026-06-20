# backend/main.py
import os
import httpx
from google import genai
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from backend.worker import review_pull_request
from backend.models import SessionLocal, PullRequest, Finding

load_dotenv()

app = FastAPI()
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
GITHUB_HEADERS = {
    "Authorization": f"token {GITHUB_TOKEN}",
    "Accept": "application/vnd.github.v3+json"
}


# --- Helper: fetch the PR diff from GitHub ---
async def fetch_pr_diff(diff_url: str) -> str:
    headers = {
        "Authorization": f"token {GITHUB_TOKEN}",
        "Accept": "application/vnd.github.v3.diff"
    }
    async with httpx.AsyncClient() as http:
        response = await http.get(diff_url, headers=headers)
        return response.text


# --- Helper: send diff to Gemini for review ---
async def review_diff_with_ai(diff: str) -> str:
    prompt = f"""
You are a senior software engineer doing a code review.
Analyze this pull request diff and list any bugs, security issues, 
or code quality problems you find.

For each issue found, format your response like this:
- File: <filename>
- Line: <line number if visible>
- Severity: critical | major | minor
- Issue: <description>
- Suggestion: <how to fix it>

If no issues are found, say "No issues found. The changes look clean."

Here is the diff:

{diff[:8000]}
"""
    response = await client.aio.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt
    )
    return response.text


# --- Helper: post the review as a comment on the PR ---
async def post_pr_comment(repo_full_name: str, pr_number: int, body: str):
    url = f"https://api.github.com/repos/{repo_full_name}/issues/{pr_number}/comments"
    payload = {"body": body}

    async with httpx.AsyncClient() as http:
        response = await http.post(url, json=payload, headers=GITHUB_HEADERS)

    if response.status_code == 201:
        print(f"Comment posted successfully to PR #{pr_number}")
    else:
        print(f"Failed to post comment: {response.status_code} — {response.text}")


# --- Format the review nicely for GitHub markdown ---
def format_review_comment(review: str, pr_title: str) -> str:
    return f"""## 🤖 AI Code Review

**PR:** {pr_title}

---

{review}

---
*Reviewed automatically by PR Review Agent using Gemini 2.5 Flash*
"""

# Allow Next.js (port 3000) to call this API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_methods=["*"],
    allow_headers=["*"]
)

# --- Webhook route: GitHub calls this when a PR is opened ---
@app.post("/webhooks/github")
async def handle_webhook(request: Request):
    payload = await request.json()

    action = payload.get("action")
    if action != "opened":
        return {"status": "ignored", "reason": f"action was '{action}', not 'opened'"}

    pr = payload.get("pull_request", {})
    pr_number = pr.get("number")
    pr_title = pr.get("title")
    diff_url = pr.get("url")
    repo_name = payload.get("repository", {}).get("full_name")

    print(f"\n--- Webhook received: PR #{pr_number} '{pr_title}' ---")
    print(f"Queuing review task...")

    # Hand off to Celery — returns instantly
    review_pull_request.delay(repo_name, pr_number, pr_title, diff_url)

    print(f"Task queued ✅ — GitHub will get 200 OK immediately")

    return {"status": "queued", "pr": f"{repo_name}#{pr_number}"}


# --- Dashboard API: all reviewed PRs ---
@app.get("/api/reviews")
async def get_reviews():
    db = SessionLocal()
    try:
        prs = db.query(PullRequest).order_by(PullRequest.reviewed_at.desc()).all()
        result = []
        for pr in prs:
            findings = db.query(Finding).filter(Finding.pr_id == pr.id).all()
            result.append({
                "id": pr.id,
                "repo_name": pr.repo_name,
                "pr_number": pr.pr_number,
                "pr_title": pr.pr_title,
                "reviewed_at": pr.reviewed_at.isoformat(),
                "total_findings": len(findings),
                "critical": sum(1 for f in findings if f.severity and "critical" in f.severity.lower()),
                "major": sum(1 for f in findings if f.severity and "major" in f.severity.lower()),
                "minor": sum(1 for f in findings if f.severity and "minor" in f.severity.lower()),
            })
        return result
    finally:
        db.close()


# --- Dashboard API: findings for a specific PR ---
@app.get("/api/reviews/{pr_id}/findings")
async def get_findings(pr_id: int):
    db = SessionLocal()
    try:
        pr = db.query(PullRequest).filter(PullRequest.id == pr_id).first()
        if not pr:
            return {"error": "PR not found"}

        findings = db.query(Finding).filter(Finding.pr_id == pr_id).all()
        return {
            "pr": {
                "id": pr.id,
                "repo_name": pr.repo_name,
                "pr_number": pr.pr_number,
                "pr_title": pr.pr_title,
                "reviewed_at": pr.reviewed_at.isoformat(),
            },
            "findings": [
                {
                    "id": f.id,
                    "file_path": f.file_path,
                    "line_number": f.line_number,
                    "severity": f.severity,
                    "issue": f.issue,
                    "suggestion": f.suggestion,
                }
                for f in findings
            ]
        }
    finally:
        db.close()


# --- Dashboard API: summary stats ---
@app.get("/api/stats")
async def get_stats():
    db = SessionLocal()
    try:
        total_prs = db.query(PullRequest).count()
        total_findings = db.query(Finding).count()
        critical = db.query(Finding).filter(Finding.severity.ilike("%critical%")).count()
        major = db.query(Finding).filter(Finding.severity.ilike("%major%")).count()
        minor = db.query(Finding).filter(Finding.severity.ilike("%minor%")).count()
        return {
            "total_prs_reviewed": total_prs,
            "total_findings": total_findings,
            "critical": critical,
            "major": major,
            "minor": minor
        }
    finally:
        db.close()

# --- Health check ---
@app.get("/health")
async def health():
    return {"status": "ok"}