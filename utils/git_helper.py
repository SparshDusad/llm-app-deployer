import os
import shutil
import subprocess
from pathlib import Path
import requests
import time
from utils.logger import get_logger

logger = get_logger(__name__)

# Environment variables
GITHUB_USERNAME = os.getenv("GITHUB_USERNAME")
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
BRANCH = os.getenv("BRANCH", "main")

MAIN_REPO = "llm-app-deployer"


# --------------------------- Utility ---------------------------

def run_cmd(cmd, check=True):
    """Run a shell command and log output."""
    logger.info(f"$ {' '.join(cmd)}")
    return subprocess.run(cmd, check=check, capture_output=True, text=True)


def create_license_file(repo_root: str):
    """Ensure an MIT LICENSE file exists."""
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
            "THE SOFTWARE IS PROVIDED \"AS IS\", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED."
        )
        license_path.write_text(mit_text)
        logger.info("✅ MIT LICENSE created.")


def ensure_git_identity():
    """Ensure Git identity is configured (needed on Render)."""
    try:
        existing_email = run_cmd(["git", "config", "user.email"], check=False).stdout.strip()
        existing_name = run_cmd(["git", "config", "user.name"], check=False).stdout.strip()
        if not existing_email or not existing_name:
            raise Exception("Missing git identity")
    except Exception:
        run_cmd(["git", "config", "--global", "user.email", f"{GITHUB_USERNAME}@users.noreply.github.com"])
        run_cmd(["git", "config", "--global", "user.name", GITHUB_USERNAME])
        logger.info("✅ Git identity configured.")


# --------------------------- Core Logic ---------------------------

def git_commit_and_push(task_folder: str, task: str, commit_msg: str) -> str:
    """
    Add, commit, and push generated code into /generated/<task> of main repo.
    Returns commit SHA.
    """
    repo_root = Path(os.getcwd())
    dest_folder = repo_root / "generated" / task
    src_folder = Path(task_folder).resolve()

    # Copy files only if source is different
    if src_folder != dest_folder.resolve():
        dest_folder.mkdir(parents=True, exist_ok=True)
        for item in os.listdir(src_folder):
            src = src_folder / item
            dest = dest_folder / item
            if src.is_dir():
                shutil.copytree(src, dest, dirs_exist_ok=True)
            else:
                shutil.copy2(src, dest)
        logger.info(f"📁 Copied new files from {src_folder} → {dest_folder}")
    else:
        logger.warning("⚠️ Source and destination are the same — skipping copy.")

    # Ensure LICENSE exists
    create_license_file(str(repo_root))

    # Ensure Git identity
    ensure_git_identity()

    # Setup remote
    remote_url = f"https://{GITHUB_USERNAME}:{GITHUB_TOKEN}@github.com/{GITHUB_USERNAME}/{MAIN_REPO}.git"
    existing_remotes = subprocess.run(["git", "remote"], capture_output=True, text=True).stdout.split()
    if "origin" not in existing_remotes:
        run_cmd(["git", "remote", "add", "origin", remote_url], check=False)
    else:
        run_cmd(["git", "remote", "set-url", "origin", remote_url], check=False)

    # Stage only the generated folder
    run_cmd(["git", "add", "generated/"], check=True)
    try:
        run_cmd(["git", "commit", "-m", commit_msg], check=True)
    except subprocess.CalledProcessError:
        logger.info("⚠️ Nothing to commit. Skipping commit.")

    # Rebase + push
    run_cmd(["git", "pull", "origin", BRANCH, "--rebase"], check=False)
    run_cmd(["git", "push", "origin", BRANCH], check=True)

    # Commit SHA
    sha = run_cmd(["git", "rev-parse", "HEAD"], check=True).stdout.strip()
    logger.info(f"✅ Git commit pushed: {sha}")
    return sha


# --------------------------- GitHub Pages ---------------------------

def enable_github_pages(repo_name: str = MAIN_REPO):
    """Enable GitHub Pages for the main repo."""
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

        # Wait for Pages build
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


# --------------------------- Auto Commit Helper ---------------------------

def auto_commit_after_api(generated_path: str, task: str, round_num: int):
    """
    Automatically commit after each API generation.
    """
    try:
        commit_message = f"Deploy {task} (Round {round_num}) | Auto-commit"
        sha = git_commit_and_push(generated_path, task, commit_message)
        enable_github_pages()
        logger.info(f"✅ Auto commit done for task {task}, commit: {sha}")
        return sha
    except Exception as e:
        logger.error(f"❌ Auto commit failed for task {task}: {e}")
        return None
