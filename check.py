# pre_submit_check.py
import os
import json
import requests
from pathlib import Path

# === CONFIG ===
USERNAME = "your-github-username"
REPO_NAME = "your-repo-name"  # e.g. llm-app-deployer-task-123
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
PAGES_URL = f"https://{USERNAME}.github.io/{REPO_NAME}/"
EVAL_PAYLOAD = "evaluation_payload.json"  # JSON you’ll POST to evaluation_url

headers = {"Authorization": f"token {GITHUB_TOKEN}"} if GITHUB_TOKEN else {}

# === STEP 1: FILE VALIDATION ===
required_files = ["index.html", "README.md", "LICENSE"]
missing = [f for f in required_files if not Path(f).exists()]
if missing:
    print(f"❌ Missing required files: {missing}")
else:
    print("✅ All required files exist")

# === STEP 2: LICENSE CHECK ===
if Path("LICENSE").exists():
    text = Path("LICENSE").read_text(encoding="utf-8")
    if "MIT License" in text or "MIT" in text:
        print("✅ MIT License verified")
    else:
        print("❌ LICENSE file exists but not MIT")
else:
    print("❌ LICENSE file not found")

# === STEP 3: README STRUCTURE ===
if Path("README.md").exists():
    readme = Path("README.md").read_text(encoding="utf-8")
    sections = ["Description", "Setup", "Usage", "Code", "License"]
    missing_sections = [s for s in sections if s.lower() not in readme.lower()]
    if missing_sections:
        print(f"⚠️ README missing sections: {missing_sections}")
    else:
        print("✅ README structure looks good")
else:
    print("❌ README.md not found")

# === STEP 4: FETCH LATEST COMMIT SHA VIA GITHUB API ===
try:
    url = f"https://api.github.com/repos/{USERNAME}/{REPO_NAME}/commits"
    resp = requests.get(url, headers=headers)
    if resp.status_code == 200:
        commit_sha = resp.json()[0]["sha"]
        print(f"✅ Latest commit SHA: {commit_sha}")
    else:
        print(f"❌ Failed to fetch commits (HTTP {resp.status_code})")
        commit_sha = None
except Exception as e:
    print(f"❌ Error fetching commit: {e}")
    commit_sha = None

# === STEP 5: CHECK GITHUB PAGES URL ===
try:
    r = requests.get(PAGES_URL, timeout=10)
    if r.status_code == 200:
        print(f"✅ GitHub Pages reachable at {PAGES_URL}")
    else:
        print(f"❌ GitHub Pages not reachable (HTTP {r.status_code})")
except Exception as e:
    print(f"❌ Error reaching GitHub Pages: {e}")

# === STEP 6: EVALUATION PAYLOAD VALIDATION ===
if Path(EVAL_PAYLOAD).exists():
    data = json.loads(Path(EVAL_PAYLOAD).read_text())
    keys = ["email", "task", "round", "nonce", "repo_url", "commit_sha", "pages_url"]
    missing_keys = [k for k in keys if k not in data]
    if missing_keys:
        print(f"❌ Payload missing keys: {missing_keys}")
    else:
        print("✅ Evaluation payload structure valid")
else:
    print("⚠️ evaluation_payload.json not found")

print("\n🎯 Pre-submission check complete.")
