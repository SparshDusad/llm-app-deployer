import os
import time
from fastapi import FastAPI, HTTPException
from models import TaskRequest, APIResponse
from builder_agent import generate_app_code
from utils.verifier import verify_secret
from utils.git_helper import git_commit_and_push, enable_github_pages
from utils.evaluator import notify_evaluator
from utils.logger import get_logger
from dotenv import load_dotenv
from pathlib import Path

load_dotenv()
logger = get_logger(__name__)
app = FastAPI(title="LLM App Deployer", version="2.0")

# Load environment variables
GITHUB_USERNAME = os.getenv("GITHUB_USERNAME")
REPO_NAME = os.getenv("REPO_NAME", "llm-app-deployer")

@app.post("/api-endpoint", response_model=APIResponse)
async def handle_task(task_req: TaskRequest):
    """
    Full deployment pipeline:
    1. Verify secret
    2. Generate app code
    3. Commit & push to GitHub
    4. Enable GitHub Pages
    5. Notify evaluator with the correct URL
    """
    logger.info(f"🚀 Received request for task '{task_req.task}' (Round {task_req.round})")

    # Step 1: Verify secret
    if not verify_secret(task_req.secret):
        logger.warning("❌ Invalid secret provided.")
        raise HTTPException(status_code=403, detail="Invalid secret")

    # Step 2: Generate app code
    attachments_list = [a.dict() for a in task_req.attachments] if task_req.attachments else []
    task_folder = str(Path("generated") / task_req.task)
    generate_app_code(task_req.task, task_req.brief, attachments_list)
    
    # Step 3: Git commit & push
    try:
        commit_sha = git_commit_and_push(
            task_folder, task_req.task, f"Deploy {task_req.task} (Round {task_req.round})"
        )
    except Exception as e:
        logger.exception("❌ Git operation failed")
        raise HTTPException(status_code=500, detail=f"Git operation failed: {e}")

    # Step 4: Enable GitHub Pages
    try:
        enable_github_pages(REPO_NAME)
    except Exception as e:
        logger.warning(f"⚠️ GitHub Pages enabling encountered an issue: {e}")

    # --- THE FIX IS HERE ---
    # Step 5: Construct the correct, specific URL to the generated app
    pages_url = f"https://{GITHUB_USERNAME}.github.io/{REPO_NAME}/generated/{task_req.task}/"
    logger.info(f"✅ Constructed correct Pages URL: {pages_url}")
    
    # Step 6: Notify evaluator with the correct URL
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
            pages_url=pages_url  # Pass the correct URL
        )
    except Exception as e:
        logger.exception("❌ Evaluator notification failed")
        raise HTTPException(status_code=500, detail=f"Evaluator notification failed: {e}")

    logger.info(f"✅ Task '{task_req.task}' deployed successfully.")

    # Step 7: Return the correct URL in the final response
    return APIResponse(
        status="success",
        message=f"✅ App deployed successfully. View it here: {pages_url}",
    )

