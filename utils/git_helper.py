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

MAIN_REPO = "llm-app-deployer"


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
    Add, commit, and push generated code into /generated/<task> of main repo.
    Returns commit SHA.
    """
    repo_root = os.getcwd()
    dest_folder = Path(repo_root) / "generated" / task
    dest_folder.parent.mkdir(parents=True, exist_ok=True)

    # Copy generated files into generated/<task> directory
    if dest_folder.exists():
        shutil.rmtree(dest_folder)
    shutil.copytree(task_folder, dest_folder, dirs_exist_ok=True)
    logger.info(f"📁 Copied generated files to {dest_folder}")

    # Ensure LICENSE exists
    create_license_file(repo_root)

    # Stage, commit, and push changes
    subprocess.run(["git", "add", "."], check=True)
    try:
        subprocess.run(["git", "commit", "-m", commit_msg], check=True)
    except subprocess.CalledProcessError:
        logger.info("⚠️ Nothing to commit. Skipping git commit.")

    # Always point to main repo
    remote_url = f"https://{GITHUB_USERNAME}:{GITHUB_TOKEN}@github.com/{GITHUB_USERNAME}/{MAIN_REPO}.git"
    subprocess.run(["git", "remote", "set-url", "origin", remote_url], check=False)

    # Push to main branch
    subprocess.run(["git", "push", "--set-upstream", "origin", BRANCH], check=True)

    # Get commit SHA
    sha = subprocess.run(["git", "rev-parse", "HEAD"], capture_output=True, text=True).stdout.strip()
    logger.info(f"✅ Git commit pushed: {sha}")

    return sha


def enable_github_pages(repo_name: str = MAIN_REPO):
    """Enable GitHub Pages for the main repo"""
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
