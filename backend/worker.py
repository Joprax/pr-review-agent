# backend/worker.py
import os
import re
import httpx
from celery import Celery
from google import genai
from dotenv import load_dotenv
from backend.models import SessionLocal, PullRequest, Finding

load_dotenv()

# --- Celery app ---
celery_app = Celery(
    "pr_review_agent",
    broker=os.getenv("REDIS_URL"),
    backend=os.getenv("REDIS_URL")
)

# --- Gemini client ---
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
GITHUB_HEADERS = {
    "Authorization": f"token {GITHUB_TOKEN}",
    "Accept": "application/vnd.github.v3+json"
}


def fetch_pr_diff(diff_url: str) -> str:
    headers = {
        "Authorization": f"token {GITHUB_TOKEN}",
        "Accept": "application/vnd.github.v3.diff"
    }
    with httpx.Client() as http:
        response = http.get(diff_url, headers=headers)
        return response.text


def review_diff_with_ai(diff: str) -> str:
    prompt = f"""
You are a senior software engineer doing a code review.
Analyze this pull request diff and list any bugs, security issues, 
or code quality problems you find.

For each issue found, format your response EXACTLY like this:
- File: <filename>
- Line: <line number if visible>
- Severity: critical | major | minor
- Issue: <description>
- Suggestion: <how to fix it>

If no issues are found, say "No issues found. The changes look clean."

Here is the diff:

{diff[:8000]}
"""
    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt
    )
    return response.text


def parse_findings(review_text: str) -> list[dict]:
    """Parse Gemini's text response into a list of structured findings."""
    findings = []
    # Split on double newline or new finding block
    blocks = re.split(r'\n(?=- File:)', review_text.strip())

    for block in blocks:
        if "- File:" not in block:
            continue
        finding = {}
        for line in block.strip().splitlines():
            line = line.strip()
            if line.startswith("- File:"):
                finding["file_path"] = line.replace("- File:", "").strip()
            elif line.startswith("- Line:"):
                finding["line_number"] = line.replace("- Line:", "").strip()
            elif line.startswith("- Severity:"):
                finding["severity"] = line.replace("- Severity:", "").strip()
            elif line.startswith("- Issue:"):
                finding["issue"] = line.replace("- Issue:", "").strip()
            elif line.startswith("- Suggestion:"):
                finding["suggestion"] = line.replace("- Suggestion:", "").strip()
        if finding:
            findings.append(finding)

    return findings


def save_review_to_db(repo_name: str, pr_number: int, pr_title: str, findings: list[dict]):
    """Save the PR and its findings to PostgreSQL."""
    db = SessionLocal()
    try:
        # Save the PR record
        pr_record = PullRequest(
            repo_name=repo_name,
            pr_number=pr_number,
            pr_title=pr_title
        )
        db.add(pr_record)
        db.flush()  # get the pr_record.id before committing

        # Save each finding
        for f in findings:
            finding_record = Finding(
                pr_id=pr_record.id,
                file_path=f.get("file_path"),
                line_number=f.get("line_number"),
                severity=f.get("severity"),
                issue=f.get("issue"),
                suggestion=f.get("suggestion")
            )
            db.add(finding_record)

        db.commit()
        print(f"✅ Saved PR #{pr_number} with {len(findings)} finding(s) to database")

    except Exception as e:
        db.rollback()
        print(f"❌ Database error: {e}")
    finally:
        db.close()


def post_pr_comment(repo_full_name: str, pr_number: int, body: str):
    url = f"https://api.github.com/repos/{repo_full_name}/issues/{pr_number}/comments"
    with httpx.Client() as http:
        response = http.post(url, json={"body": body}, headers=GITHUB_HEADERS)
    if response.status_code == 201:
        print(f"✅ Comment posted to PR #{pr_number}")
    else:
        print(f"❌ Failed to post comment: {response.status_code} — {response.text}")


def format_review_comment(review: str, pr_title: str) -> str:
    return f"""## 🤖 AI Code Review

**PR:** {pr_title}

---

{review}

---
*Reviewed automatically by PR Review Agent using Gemini 2.5 Flash*
"""


# --- The Celery task ---
@celery_app.task
def review_pull_request(repo_name: str, pr_number: int, pr_title: str, diff_url: str):
    print(f"\n[Celery] Starting review for PR #{pr_number}: {pr_title}")

    diff = fetch_pr_diff(diff_url)
    print(f"[Celery] Diff fetched — {len(diff)} characters")

    review = review_diff_with_ai(diff)
    print(f"[Celery] Review complete:\n{review}")

    # Parse findings and save to database
    findings = parse_findings(review)
    print(f"[Celery] Parsed {len(findings)} finding(s)")
    save_review_to_db(repo_name, pr_number, pr_title, findings)

    # Post comment to GitHub
    comment = format_review_comment(review, pr_title)
    post_pr_comment(repo_name, pr_number, comment)

    print(f"[Celery] Task complete for PR #{pr_number}")
    return {"status": "done", "pr": pr_number, "findings": len(findings)}