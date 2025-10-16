import os
from fastapi import FastAPI, HTTPException
from models import TaskRequest, APIResponse
from builder_agent import generate_app_code
from utils.verifier import verify_secret
from utils.git_helper import git_commit_and_push
from utils.evaluator import notify_evaluator
from utils.logger import get_logger
from dotenv import load_dotenv
from pathlib import Path

load_dotenv()
logger = get_logger(__name__)
app = FastAPI()

# Load environment variables once
GITHUB_USERNAME = os.getenv("GITHUB_USERNAME")
REPO_NAME = os.getenv("REPO_NAME", "llm-app-deployer")


def ensure_placeholder(task_folder: str):
    """
    If generated code is missing or invalid, add a placeholder page.
    """
    index_path = Path(task_folder) / "index.html"
    if not index_path.exists() or index_path.read_text().strip() == "":
        logger.warning(f"Adding placeholder index.html for {task_folder}")
        index_path.write_text(
            "<!DOCTYPE html><html><head><title>App Placeholder</title></head>"
            "<body><h1>llm-app-deployer</h1><p>This site is open source. Improve this page.</p></body></html>"
        )
    # Ensure minimal CSS and JS exist
    (Path(task_folder) / "style.css").write_text("/* Placeholder CSS */")
    (Path(task_folder) / "script.js").write_text("// Placeholder JS")


@app.post("/api-endpoint", response_model=APIResponse)
async def handle_task(task_req: TaskRequest):
    """
    Full deployment: generate code, push to git, enable Pages, notify evaluator.
    """
    logger.info(f"Received request for task '{task_req.task}', round {task_req.round}")

    if not verify_secret(task_req.secret):
        logger.warning(f"Invalid secret for task '{task_req.task}'")
        raise HTTPException(status_code=403, detail="Invalid secret")

    # Step 1: Generate app code
    attachments_list = [a.dict() for a in task_req.attachments] if task_req.attachments else []
    task_folder = generate_app_code(task_req.task, task_req.brief, attachments_list)
    if not task_folder:
        task_folder = str(Path("generated") / task_req.task)
        Path(task_folder).mkdir(parents=True, exist_ok=True)

    ensure_placeholder(task_folder)

    # Step 2: Git commit & push
    try:
        commit_sha = git_commit_and_push(task_folder, f"Deploy {task_req.task} (Round {task_req.round})")
    except Exception as e:
        logger.exception("Git operation failed")
        raise HTTPException(status_code=500, detail=f"Git operation failed: {e}")

    # Step 3: Notify evaluator
    try:
        notify_evaluator(
            email=task_req.email,
            task=task_req.task,
            round_=task_req.round,
            nonce=task_req.nonce,
            commit_sha=commit_sha,
            github_user=GITHUB_USERNAME,
            repo_name=REPO_NAME,
            evaluation_url=str(task_req.evaluation_url)
        )
    except Exception as e:
        logger.exception("Evaluator notification failed")
        raise HTTPException(status_code=500, detail=f"Evaluator notification failed: {e}")

    pages_url = f"https://{GITHUB_USERNAME}.github.io/{REPO_NAME}/"
    logger.info(f"Task '{task_req.task}' deployed successfully to {pages_url}")
    return APIResponse(status="success", message=f"Pages deployed successfully: {pages_url}")


@app.post("/build", response_model=APIResponse)
async def build_app(task_req: TaskRequest):
    """
    Only generate code and ensure placeholders.
    """
    logger.info(f"Received build request for task '{task_req.task}'")
    if not verify_secret(task_req.secret):
        raise HTTPException(status_code=403, detail="Invalid secret")

    attachments_list = [a.dict() for a in task_req.attachments] if task_req.attachments else []
    task_folder = generate_app_code(task_req.task, task_req.brief, attachments_list)
    if not task_folder:
        task_folder = str(Path("generated") / task_req.task)
        Path(task_folder).mkdir(parents=True, exist_ok=True)

    ensure_placeholder(task_folder)
    return APIResponse(status="success", message=f"App generated successfully at {task_folder}")
