import os
import shutil
import subprocess
from pathlib import Path
from utils.logger import get_logger
import requests
import time

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


def git_commit_and_push(task_folder: str, task: str, commit_msg: str) -> str:
    """
    Add, commit, push generated code (Round 1 or 2) and ensure LICENSE/README.
    Returns commit SHA.
    """
    repo_root = os.getcwd()  # Assume current working dir is repo root
    repo_name = task  # dynamic repo name

    # Copy all generated files (including README.md) to repo root
    for item in os.listdir(task_folder):
        src = os.path.join(task_folder, item)
        dest = os.path.join(repo_root, item)
        if os.path.isdir(src):
            shutil.copytree(src, dest, dirs_exist_ok=True)
        else:
            shutil.copy2(src, dest)

    # Ensure LICENSE exists
    create_license_file(repo_root)

    # Stage all changes
    subprocess.run(["git", "add", "."], check=True)

    # Commit changes
    try:
        subprocess.run(["git", "commit", "-m", commit_msg], check=True)
    except subprocess.CalledProcessError:
        logger.info("⚠️ Nothing to commit. Skipping git commit.")

    # Add remote if missing
    remote_url = f"https://{GITHUB_USERNAME}:{GITHUB_TOKEN}@github.com/{GITHUB_USERNAME}/{repo_name}.git"
    subprocess.run(["git", "remote", "add", "origin", remote_url], check=False)

    # Push to branch
    subprocess.run(["git", "push", "--set-upstream", "origin", BRANCH], check=True)

    # Get latest commit SHA
    sha = subprocess.run(["git", "rev-parse", "HEAD"], capture_output=True, text=True).stdout.strip()
    logger.info(f"✅ Git commit pushed: {sha}")

    return sha


def enable_github_pages(repo_name: str):
    """Enable GitHub Pages for the repo and wait until built"""
    import requests

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

        # Wait for Pages to build
        pages_url = f"https://api.github.com/repos/{GITHUB_USERNAME}/{repo_name}/pages/builds/latest"
        for _ in range(10):
            r = requests.get(pages_url, auth=(GITHUB_USERNAME, GITHUB_TOKEN))
            if r.status_code == 200 and r.json().get("status") == "built":
                logger.info("🌐 GitHub Pages is active.")
                return
            logger.info("⏳ Waiting for Pages to build...")
            time.sleep(5)
        logger.warning("⚠️ GitHub Pages not fully built yet.")
    except Exception as e:
        logger.error(f"Exception enabling GitHub Pages: {e}")
