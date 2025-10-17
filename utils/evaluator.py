import requests
import json
import time
from pathlib import Path
from utils.logger import get_logger

logger = get_logger(__name__)

def notify_evaluator(
    email: str,
    task: str,
    round_: int,
    nonce: str,
    commit_sha: str,
    github_user: str,
    repo_name: str,
    evaluation_url: str,
    pages_url: str  # This parameter was missing
) -> dict:
    """
    Notify the evaluator that a deployment is ready for evaluation.
    
    Now accepts a specific pages_url to ensure the correct link is sent.
    """

    repo_url = f"https://github.com/{github_user}/{repo_name}"

    # The payload now uses the pages_url passed directly into the function.
    payload = {
        "email": email,
        "task": task,
        "round": round_,
        "nonce": nonce,
        "repo_url": repo_url,
        "commit_sha": commit_sha,
        "pages_url": pages_url
    }

    # --- Step 1: Save payload locally ---
    output_path = Path("generated") / task / "evaluation_payload.json"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(payload, indent=2))
    logger.info(f"✅ Saved evaluation payload at: {output_path.resolve()}")

    # --- Step 2: Attempt to notify evaluator API ---
    logger.info(f"🚀 Notifying evaluator at {evaluation_url}")
    logger.debug(f"Payload: {payload}")

    max_retries = 3
    for attempt in range(1, max_retries + 1):
        try:
            response = requests.post(evaluation_url, json=payload, timeout=30)
            if response.status_code == 200:
                logger.info(f"✅ Evaluator notified successfully (attempt {attempt})")
                logger.debug(f"Evaluator response: {response.text}")
                break
            else:
                logger.warning(f"⚠️ Attempt {attempt}: Received HTTP {response.status_code} - {response.text}")
        except requests.RequestException as e:
            logger.error(f"❌ Attempt {attempt} failed: {e}")
        if attempt < max_retries:
            logger.info("⏳ Retrying in 5 seconds...")
            time.sleep(5)
    else:
        logger.error("❌ All attempts to notify evaluator failed after retries.")
        raise RuntimeError("Failed to notify evaluator after multiple attempts.")

    return payload

