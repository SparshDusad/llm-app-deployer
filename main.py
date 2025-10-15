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
# Create a logger instance for the application
logger = get_logger(__name__)
app = FastAPI()

# Load environment variables once
GITHUB_USERNAME = os.getenv("GITHUB_USERNAME")
REPO_NAME = os.getenv("REPO_NAME", "llm-app-deployer")


@app.post("/api-endpoint", response_model=APIResponse)
async def handle_task(task_req: TaskRequest):
    """
    Handles the full process: generate code, push to git, and notify evaluator.
    """
    logger.info(f"Received request for full deployment of task: {task_req.task}")
    
    # --- Step 1: Verify secret ---
    if not verify_secret(task_req.secret):
        logger.warning(f"Invalid secret received for task: {task_req.task}")
        raise HTTPException(status_code=403, detail="Invalid secret")

    # --- Step 2: Generate app code using Gemini ---
    try:
        # CORRECTED: Convert attachments from Pydantic models to dicts
        attachments_list = [a.dict() for a in task_req.attachments] if task_req.attachments else []
        task_folder = generate_app_code(task_req.task, task_req.brief, attachments_list)
        if not task_folder:
            logger.error("Code generation returned an empty path.")
            raise HTTPException(status_code=500, detail="Failed to generate app code")
    except Exception as e:
        logger.exception("An error occurred during code generation.")
        raise HTTPException(status_code=500, detail=f"Failed to generate app code: {e}")

    # --- Step 3: Git commit & push ---
    try:
        commit_sha = git_commit_and_push(task_folder, f"Deploy {task_req.task} (Round {task_req.round})")
    except Exception as e:
        logger.exception("An error occurred during git push.")
        # The original RuntimeError from git_helper will be caught here.
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
        logger.exception("An error occurred notifying the evaluator.")
        raise HTTPException(status_code=500, detail=f"Evaluation API failed: {e}")

    pages_url = f"https://{GITHUB_USERNAME}.github.io/{REPO_NAME}/"
    logger.info(f"Task '{task_req.task}' deployed successfully to {pages_url}")
    return APIResponse(status="success", message=f"Pages deployed successfully: {pages_url}")


@app.post("/build", response_model=APIResponse)
async def build_app(request: TaskRequest):
    """
    Handles only the code generation part of the task.
    """
    try:
        if not verify_secret(request.secret):
            logger.warning(f"Invalid secret received for build task: {request.task}")
            raise HTTPException(status_code=403, detail="Invalid secret")

        # CORRECTED: Use the 'logger' instance
        logger.info(f"Received build request for task: {request.task}")

        attachments_list = [a.dict() for a in request.attachments] if request.attachments else []
        output_path = generate_app_code(request.task, request.brief, attachments_list)

        if not output_path:
            logger.error(f"Code generation failed for build task: {request.task}")
            raise HTTPException(status_code=500, detail="Failed to generate app code")
        
        message = f"App generated successfully at {output_path}"
        logger.info(message)
        return APIResponse(status="success", message=message)

    except Exception as e:
        # CORRECTED: Use the 'logger' instance
        logger.exception("Unhandled error in /build endpoint")
        raise HTTPException(status_code=500, detail=str(e))
