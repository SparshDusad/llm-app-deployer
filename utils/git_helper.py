import os
import shutil
import subprocess
from pathlib import Path
import requests
import time
from utils.logger import get_logger

logger = get_logger(__name__)

# Load environment variables
GITHUB_USERNAME = os.getenv("GITHUB_USERNAME")
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
BRANCH = os.getenv("BRANCH", "main")
REPO_NAME = os.getenv("REPO_NAME", "llm-app-deployer")


def run_cmd(cmd, check=True, cwd=None):
    """Run a shell command, log it, and return its output."""
    logger.info(f"Executing command: {' '.join(cmd)}")
    try:
        result = subprocess.run(
            cmd,
            check=check,
            capture_output=True,
            text=True,
            cwd=cwd
        )
        if result.stdout:
            logger.info(result.stdout)
        if result.stderr:
            logger.warning(result.stderr)
        return result
    except subprocess.CalledProcessError as e:
        logger.error(f"Command failed: {' '.join(e.cmd)}")
        logger.error(f"Stderr: {e.stderr}")
        logger.error(f"Stdout: {e.stdout}")
        raise


def ensure_git_identity(repo_root):
    """Ensure Git user.name and user.email are configured for the repo."""
    logger.info("Configuring git user details...")
    run_cmd(["git", "config", "user.name", GITHUB_USERNAME], cwd=repo_root)
    run_cmd(["git", "config", "user.email", f"{GITHUB_USERNAME}@users.noreply.github.com"], cwd=repo_root)


def git_commit_and_push(task_folder: str, task: str, commit_msg: str) -> str:
    """
    Adds, commits, and pushes a specific folder to a GitHub repository.
    This function is safe to run multiple times.

    Returns:
        str: The SHA of the new commit.
    """
    repo_root = os.getcwd()
    
    ensure_git_identity(repo_root)

    # Set or Update the Remote URL (Idempotent)
    remote_url = f"https://{GITHUB_USERNAME}:{GITHUB_TOKEN}@github.com/{GITHUB_USERNAME}/{REPO_NAME}.git"
    remotes = run_cmd(["git", "remote"], cwd=repo_root).stdout.splitlines()

    if "origin" in remotes:
        logger.info("Remote 'origin' already exists. Setting URL.")
        run_cmd(["git", "remote", "set-url", "origin", remote_url], cwd=repo_root)
    else:
        logger.info("Remote 'origin' not found. Adding it.")
        run_cmd(["git", "remote", "add", "origin", remote_url], cwd=repo_root)

    # Add, Commit, and Push
    logger.info(f"Adding folder to git: {task_folder}")
    # Use -f to force add if it's in .gitignore
    run_cmd(["git", "add", "-f", task_folder], cwd=repo_root)
    
    # Check for changes before committing
    status_result = run_cmd(["git", "status", "--porcelain"], cwd=repo_root)
    if not status_result.stdout:
        logger.warning("⚠️ No changes to commit. Skipping commit and push.")
        return run_cmd(["git", "rev-parse", "HEAD"], cwd=repo_root).stdout.strip()
        
    logger.info(f"Committing with message: '{commit_msg}'")
    run_cmd(["git", "commit", "-m", commit_msg], cwd=repo_root)
    
    logger.info(f"Pushing to origin/{BRANCH}...")
    run_cmd(["git", "push", "origin", BRANCH], cwd=repo_root)

    # Get the Commit SHA
    sha = run_cmd(["git", "rev-parse", "HEAD"], cwd=repo_root).stdout.strip()

    logger.info(f"✅ Successfully pushed commit with SHA: {sha}")
    return sha


def enable_github_pages(repo_name: str):
    """Enable GitHub Pages for the main repo."""
    url = f"https://api.github.com/repos/{GITHUB_USERNAME}/{repo_name}/pages"
    headers = {
        "Authorization": f"token {GITHUB_TOKEN}",
        "Accept": "application/vnd.github.v3+json"
    }
    data = {"source": {"branch": BRANCH, "path": "/"}}

    logger.info("Attempting to enable GitHub Pages...")
    response = requests.post(url, headers=headers, json=data)

    if response.status_code == 201:
        logger.info("✅ GitHub Pages enabled successfully.")
    elif response.status_code == 409:
        logger.info("⚠️ GitHub Pages was already enabled.")
    else:
        logger.error(f"❌ Failed to enable GitHub Pages: {response.status_code} - {response.text}")
        # Even if it fails, don't crash the whole process
    
    # It takes time for the pages to build, this is just an initial trigger

