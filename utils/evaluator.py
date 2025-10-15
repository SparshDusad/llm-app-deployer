import requests
from utils.logger import get_logger

logger = get_logger(__name__)


def notify_evaluator(email: str, task: str, round_: int, nonce: str, commit_sha: str, github_user: str, repo_name: str, evaluation_url: str) -> dict:
    """Send deployment details to the evaluation API."""
    pages_url = f"https://{github_user}.github.io/{repo_name}/"
    repo_url = f"https://github.com/{github_user}/{repo_name}"
    
    payload = {
        "email": email,
        "task": task,
        "round": round_,
        "nonce": nonce,
        "repo_url": repo_url,
        "commit_sha": commit_sha,
        "pages_url": pages_url
    }

    logger.info(f"Notifying evaluator for task '{task}' at {evaluation_url}")
    logger.debug(f"Payload: {payload}")

    try:
        resp = requests.post(evaluation_url, json=payload, timeout=30)
        # This will raise an HTTPError for bad responses (4xx or 5xx)
        resp.raise_for_status()
    except requests.RequestException as e:
        logger.error(f"Failed to notify evaluator: {e}")
        # Re-raise the exception to be handled by the main app
        raise

    logger.info(f"Evaluator notified successfully for task '{task}'")
    return payload
