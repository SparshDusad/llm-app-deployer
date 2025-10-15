import os
from fastapi import FastAPI, HTTPException
from models import TaskRequest, APIResponse
from builder_agent import generate_app_code
from utils.verifier import verify_secret
from utils.git_helper import git_commit_and_push
from utils.evaluator import notify_evaluator
from utils.logger import get_logger
from dotenv import load_dotenv

load_dotenv()
logger = get_logger(__name__)
app = FastAPI()

GITHUB_USERNAME = os.getenv("GITHUB_USERNAME")
REPO_NAME = os.getenv("REPO_NAME", "llm-app-deployer")


@app.post("/api-endpoint", response_model=APIResponse)
async def handle_task(task_req: TaskRequest):
    """
    Handles initial deployment (round 1) and revision updates (round 2+).
    """
    logger.info(f"Received request for task '{task_req.task}', round {task_req.round}")

    # --- Step 1: Verify secret ---
    if not verify_secret(task_req.secret):
        logger.warning(f"Invalid secret for task '{task_req.task}'")
        raise HTTPException(status_code=403, detail="Invalid secret")

    # --- Step 2: Generate or update code ---
    try:
        attachments_list = [a.dict() for a in task_req.attachments] if task_req.attachments else []
        task_folder = generate_app_code(task_req.task, task_req.brief, attachments_list)
        if not task_folder:
            logger.error("Code generation returned empty folder")
            raise HTTPException(status_code=500, detail="Failed to generate app code")
    except Exception as e:
        logger.exception("Error during code generation")
        raise HTTPException(status_code=500, detail=f"Code generation failed: {e}")

    # --- Step 3: Git commit & push ---
    try:
        commit_sha = git_commit_and_push(task_folder, f"Deploy {task_req.task} (Round {task_req.round})")
    except Exception as e:
        logger.exception("Git operation failed")
        raise HTTPException(status_code=500, detail=f"Git operation failed: {e}")

    # --- Step 4: Notify evaluator ---
    try:
        notify_evaluator(
            email=task_req.email,
            task=task_req.task,
            round_=task_req.round,
            nonce=task_req.nonce,
            commit_sha=commit_sha,
            github_user=GITHUB_USERNAME,
            repo_name=REPO_NAME,
            evaluation_url=task_req.evaluation_url
        )
    except Exception as e:
        logger.exception("Evaluator notification failed")
        raise HTTPException(status_code=500, detail=f"Evaluator notification failed: {e}")

    pages_url = f"https://{GITHUB_USERNAME}.github.io/{REPO_NAME}/"
    logger.info(f"Task '{task_req.task}' deployed successfully to {pages_url}")
    return APIResponse(
        status="success",
        message=f"Pages deployed successfully (round {task_req.round}): {pages_url}"
    )
