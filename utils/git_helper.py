import os
import shutil
import subprocess
import requests
from utils.logger import get_logger

logger = get_logger(__name__)

GITHUB_USERNAME = os.getenv("GITHUB_USERNAME")
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
REPO_NAME = os.getenv("REPO_NAME", "llm-app-deployer")
BRANCH = os.getenv("BRANCH", "main")


def enable_github_pages():
    """Enable GitHub Pages for the repository."""
    url = f"https://api.github.com/repos/{GITHUB_USERNAME}/{REPO_NAME}/pages"
    data = {"source": {"branch": BRANCH, "path": "/"}}

    try:
        resp = requests.post(url, json=data, auth=(GITHUB_USERNAME, GITHUB_TOKEN))
        if resp.status_code in (201, 202):
            logger.info("GitHub Pages enabled successfully.")
        elif resp.status_code == 409:
            logger.info("GitHub Pages already enabled.")
        else:
            logger.warning(f"Failed to enable GitHub Pages: {resp.status_code} {resp.text}")
    except Exception as e:
        logger.error(f"Exception while enabling GitHub Pages: {e}")


def git_commit_and_push(task_folder: str, commit_msg: str) -> str:
    """
    Add, commit, and push generated app code to GitHub.
    Dynamically copies task_folder contents to repo root before commit.
    """
    repo_root = os.getcwd()  # Assume current working dir is repo root

    try:
        # Copy all generated files from task_folder to repo root dynamically
        for item in os.listdir(task_folder):
            src = os.path.join(task_folder, item)
            dest = os.path.join(repo_root, item)
            if os.path.isdir(src):
                shutil.copytree(src, dest, dirs_exist_ok=True)
            else:
                shutil.copy2(src, dest)

        # Stage all changes
        subprocess.run(["git", "add", "."], check=True)

        # Commit
        subprocess.run(["git", "commit", "-m", commit_msg], check=True)

        # Add remote if it doesn't exist
        remote_url = f"https://{GITHUB_USERNAME}:{GITHUB_TOKEN}@github.com/{GITHUB_USERNAME}/{REPO_NAME}.git"
        subprocess.run(["git", "remote", "add", "origin", remote_url], check=False)

        # Push to main branch
        subprocess.run(["git", "push", "--set-upstream", "origin", BRANCH], check=True)

        # Get latest commit SHA
        sha = subprocess.run(["git", "rev-parse", "HEAD"], capture_output=True, text=True).stdout.strip()
        logger.info(f"Git commit pushed with SHA: {sha}")

        # Enable GitHub Pages
        enable_github_pages()

        return sha

    except subprocess.CalledProcessError as e:
        logger.error(f"Git operation failed: {e}")
        raise RuntimeError(f"Git operation failed: {e}")
    except Exception as e:
        logger.error(f"Unexpected error during Git push: {e}")
        raise RuntimeError(f"Unexpected Git error: {e}")
