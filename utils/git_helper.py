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
    """Run a shell command, log it, and handle its output."""
    logger.info(f"Executing: {' '.join(cmd)}")
    try:
        result = subprocess.run(
            cmd,
            check=check,
            capture_output=True,
            text=True,
            cwd=cwd
        )
        if result.stdout:
            logger.info(f"Stdout: {result.stdout.strip()}")
        if result.stderr:
            logger.warning(f"Stderr: {result.stderr.strip()}")
        return result
    except subprocess.CalledProcessError as e:
        logger.error(f"Command failed with exit code {e.returncode}: {' '.join(e.cmd)}")
        logger.error(f"Stderr: {e.stderr.strip()}")
        raise


def ensure_git_identity(repo_root):
    """Ensure Git user.name and user.email are configured."""
    logger.info("Configuring git user identity...")
    run_cmd(["git", "config", "user.name", GITHUB_USERNAME], cwd=repo_root)
    run_cmd(["git", "config", "user.email", f"{GITHUB_USERNAME}@users.noreply.github.com"], cwd=repo_root)


def git_commit_and_push(task_folder: str, task: str, commit_msg: str) -> str:
    """
    Forcefully adds, commits, and pushes a folder to the GitHub repository.
    """
    if not GITHUB_USERNAME or not GITHUB_TOKEN:
        raise ValueError("Missing GITHUB_USERNAME or GITHUB_TOKEN environment variables.")

    repo_root = os.getcwd()
    ensure_git_identity(repo_root)

    # Set or Update the Remote URL
    remote_url = f"https://{GITHUB_USERNAME}:{GITHUB_TOKEN}@github.com/{GITHUB_USERNAME}/{REPO_NAME}.git"
    remotes_result = run_cmd(["git", "remote"], cwd=repo_root)
    if "origin" in remotes_result.stdout:
        run_cmd(["git", "remote", "set-url", "origin", remote_url], cwd=repo_root)
    else:
        run_cmd(["git", "remote", "add", "origin", remote_url], cwd=repo_root)

    # --- FIX ---
    # Forcefully add the specified folder. This will add new/modified files
    # even if the folder is listed in .gitignore.
    logger.info(f"Forcefully adding folder to git: {task_folder}")
    run_cmd(["git", "add", "-f", task_folder], cwd=repo_root)

    # Commit the changes. Using --allow-empty ensures a commit is made
    # which can be useful for triggering deployments even if file content is the same.
    logger.info(f"Committing with message: '{commit_msg}'")
    run_cmd(["git", "commit", "--allow-empty", "-m", commit_msg], cwd=repo_root)
    
    logger.info(f"Pushing to origin/{BRANCH}...")
    run_cmd(["git", "push", "origin", BRANCH], cwd=repo_root)

    sha = run_cmd(["git", "rev-parse", "HEAD"], cwd=repo_root).stdout.strip()
    logger.info(f"✅ Successfully pushed commit with SHA: {sha}")
    return sha


def enable_github_pages(repo_name: str):
    # This function remains the same as your previous version
    url = f"https://api.github.com/repos/{GITHUB_USERNAME}/{repo_name}/pages"
    headers = {"Authorization": f"token {GITHUB_TOKEN}", "Accept": "application/vnd.github.v3+json"}
    data = {"source": {"branch": BRANCH, "path": "/"}}
    
    logger.info("Attempting to enable GitHub Pages...")
    response = requests.post(url, headers=headers, json=data)
    
    if response.status_code == 201:
        logger.info("✅ GitHub Pages enabled successfully.")
    elif response.status_code == 409:
        logger.info("⚠️ GitHub Pages was already enabled.")
    else:
        logger.error(f"❌ Failed to enable GitHub Pages: {response.status_code} - {response.text}")

