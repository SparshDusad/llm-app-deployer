import os
from fastapi import FastAPI, Request
from dotenv import load_dotenv

from builder_agent import generate_app_code, update_app_code
from models import TaskRequest, APIResponse
from utils.logger import get_logger
from utils.git_helper import git_commit_and_push
from utils.evaluator import notify_evaluator
from utils.verifier import verify_secret

# ---------------------------------------------------
# 🔹 Setup
# ---------------------------------------------------
load_dotenv()
logger = get_logger(__name__)

GITHUB_USERNAME = os.getenv("GITHUB_USERNAME")
REPO_NAME = os.getenv("REPO_NAME", "llm-app-deployer")

app = FastAPI(title="LLM App Deployer", version="1.0")


# ---------------------------------------------------
# 🔹 Main API Endpoint
# ---------------------------------------------------
@app.post("/api-endpoint", response_model=APIResponse)
async def handle_request(request: Request):
    """
    Phase 1 (Build) and Phase 3 (Revise) unified handler.
    - Verifies secret
    - Generates or updates app
    - Commits & pushes to GitHub
    - Notifies evaluator
    """
    try:
        data = await request.json()
        task_req = TaskRequest(**data)
    except Exception as e:
        logger.error(f"Invalid request payload: {e}")
        return APIResponse(status="error", message="Invalid JSON structure")

    # --- Step 1: Verify Secret ---
    if not verify_secret(task_req.secret):
        logger.warning(f"Unauthorized request for task '{task_req.task}'")
        return APIResponse(status="error", message="Invalid secret key")

    logger.info(f"✅ Received task '{task_req.task}' | Round {task_req.round}")

    # --- Step 2: Generate or Update App ---
    try:
        if task_req.round == 1:
            logger.info("🧠 Generating initial app (Round 1)...")
            app_path = generate_app_code(task_req.task, task_req.brief, task_req.attachments)
        else:
            logger.info("🔁 Updating app (Round 2 or later)...")
            app_path = update_app_code(task_req.task, task_req.brief, task_req.attachments)
    except Exception as e:
        logger.error(f"App generation error: {e}")
        return APIResponse(status="error", message="App generation failed")

    if not app_path:
        return APIResponse(status="error", message="No app files generated")

    # --- Step 3: Git Commit & Push ---
    try:
        commit_message = f"Deploy {task_req.task} (Round {task_req.round})"
        commit_sha = git_commit_and_push(app_path, commit_message)
    except Exception as e:
        logger.error(f"Git operation failed: {e}")
        return APIResponse(status="error", message="Git commit/push failed")

    # --- Step 4: Notify Evaluator ---
    try:
        notify_evaluator(
            email=task_req.email,
            task=task_req.task,
            round_=task_req.round,
            nonce=task_req.nonce,
            commit_sha=commit_sha,
            github_user=GITHUB_USERNAME,
            repo_name=REPO_NAME,
            evaluation_url=str(task_req.evaluation_url),
        )
    except Exception as e:
        logger.error(f"Evaluator notification failed: {e}")
        return APIResponse(status="warning", message="App deployed but evaluator not notified")

    # --- Step 5: Success Response ---
    pages_url = f"https://{GITHUB_USERNAME}.github.io/{REPO_NAME}/"
    logger.info(f"🎉 Deployment complete for '{task_req.task}' → {pages_url}")

    return APIResponse(
        status="success",
        message=f"Task '{task_req.task}' (Round {task_req.round}) deployed successfully. "
                f"View your app at: {pages_url}"
    )


# ---------------------------------------------------
# 🔹 Health Check (Optional)
# ---------------------------------------------------
@app.get("/")
def health():
    return {"status": "ok", "message": "LLM App Deployer is running 🚀"}
