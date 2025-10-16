import os
import shutil
import subprocess
import requests
from pathlib import Path
from utils.logger import get_logger

logger = get_logger(__name__)

GITHUB_USERNAME = os.getenv("GITHUB_USERNAME")
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
BRANCH = os.getenv("BRANCH", "main")


def create_license_file(repo_root: str):
    """Add MIT LICENSE if not present"""
    license_path = Path(repo_root) / "LICENSE"
    if not license_path.exists():
        mit_text = (
            "MIT License\n\n"
            "Permission is hereby granted, free of charge, to any person obtaining a copy "
            "of this software and associated documentation files (the \"Software\"), to deal "
            "in the Software without restriction, including without limitation the rights "
            "to use, copy, modify, merge, publish, distribute, sublicense, and/or sell "
            "copies of the Software, and to permit persons to whom the Software is "
            "furnished to do so, subject to the following conditions:\n\n"
            "THE SOFTWARE IS PROVIDED \"AS IS\", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED..."
        )
        license_path.write_text(mit_text)
        logger.info("✅ MIT LICENSE created.")


def create_readme(repo_root: str, task: str):
    """Generate a complete README.md"""
    readme_path = Path(repo_root) / "README.md"
    if not readme_path.exists():
        readme_content = f"""# {task}

## Summary
This repository contains a minimal web app generated automatically by LLM App Deployer.

## Setup
1. Clone this repo: `git clone https://github.com/{GITHUB_USERNAME}/{task}.git`
2. Install dependencies if any.
3. Open `index.html` in browser.

## Usage
- Navigate to `index.html`.
- All JS/CSS is included locally.
- Attachments are preloaded if provided in the task.

## Code Explanation
- `index.html` – main HTML page
- `style.css` – styles
- `script.js` – frontend JS
- `evaluation_payload.json` – payload sent to evaluator

## License
MIT License
"""
        readme_path.write_text(readme_content)
        logger.info("✅ README.md generated.")


def enable_github_pages(repo_name: str):
    """Enable GitHub Pages and wait until built"""
    url = f"https://api.github.com/repos/{GITHUB_USERNAME}/{repo_name}/pages"
    data = {"source": {"branch": BRANCH, "path": "/"}}

    try:
        resp = requests.post(url, json=data, auth=(GITHUB_USERNAME, GITHUB_TOKEN))
        if resp.status_code in (201, 202):
            logger.info("✅ GitHub Pages enabled successfully.")
        elif resp.status_code == 409:
            logger.info("⚠️ GitHub Pages already enabled.")
        else:
            logger.warning(f"⚠️ Failed to enable Pages: {resp.status_code} {resp.text}")
            return

        # Poll Pages API until built
        pages_url = f"https://api.github.com/repos/{GITHUB_USERNAME}/{repo_name}/pages/builds/latest"
        for i in range(10):
            r = requests.get(pages_url, auth=(GITHUB_USERNAME, GITHUB_TOKEN))
            if r.status_code == 200 and r.json().get("status") == "built":
                logger.info("🌐 GitHub Pages is active.")
                return
            logger.info("⏳ Waiting for Pages to build...")
            time.sleep(5)
        logger.warning("⚠️ GitHub Pages not fully built yet.")
    except Exception as e:
        logger.error(f"Exception enabling GitHub Pages: {e}")


def git_commit_and_push(task_folder: str, task: str, commit_msg: str) -> str:
    """Add, commit, push generated code and ensure LICENSE/README"""
    repo_root = os.getcwd()  # Assume current working dir is repo root
    repo_name = f"{task}"  # dynamic repo name

    # Copy generated files to repo root
    for item in os.listdir(task_folder):
        src = os.path.join(task_folder, item)
        dest = os.path.join(repo_root, item)
        if os.path.isdir(src):
            shutil.copytree(src, dest, dirs_exist_ok=True)
        else:
            shutil.copy2(src, dest)

    # Create LICENSE and README
    create_license_file(repo_root)
    create_readme(repo_root, task)

    # Git operations
    subprocess.run(["git", "add", "."], check=True)
    subprocess.run(["git", "commit", "-m", commit_msg], check=True)
    remote_url = f"https://{GITHUB_USERNAME}:{GITHUB_TOKEN}@github.com/{GITHUB_USERNAME}/{repo_name}.git"
    subprocess.run(["git", "remote", "add", "origin", remote_url], check=False)
    subprocess.run(["git", "push", "--set-upstream", "origin", BRANCH], check=True)

    sha = subprocess.run(["git", "rev-parse", "HEAD"], capture_output=True, text=True).stdout.strip()
    logger.info(f"✅ Git commit pushed: {sha}")

    enable_github_pages(repo_name)
    return sha
