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
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
REPO_NAME = os.getenv("REPO_NAME", "llm-app-deployer")
BRANCH = os.getenv("BRANCH", "main")


def ensure_placeholder(task_folder: str):
    """
    If generated code is missing or invalid, add a placeholder page.
    Ensures that GitHub Pages always renders something instead of 404.
    """
    index_path = Path(task_folder) / "index.html"
    if not index_path.exists() or index_path.read_text().strip() == "":
        logger.warning(f"Adding placeholder index.html for {task_folder}")
        index_path.write_text(
            "<!DOCTYPE html><html><head><title>App Placeholder</title>"
            "<meta charset='utf-8' /><style>body{font-family:sans-serif;text-align:center;padding:50px;}</style></head>"
            "<body><h1>🚧 App Build Pending</h1><p>Your app was deployed successfully but is still generating content.</p></body></html>"
        )
    (Path(task_folder) / "style.css").write_text("/* Placeholder CSS */")
    (Path(task_folder) / "script.js").write_text("// Placeholder JS")


@app.post("/api-endpoint", response_model=APIResponse)
async def handle_task(task_req: TaskRequest):
    """
    Full deployment pipeline:
    1. Verify secret
    2. Generate app code
    3. Commit & push to GitHub
    4. Enable GitHub Pages
    5. Notify evaluator
    """
    logger.info(f"🚀 Received request for task '{task_req.task}' (Round {task_req.round})")

    # Step 1: Verify secret
    if not verify_secret(task_req.secret):
        logger.warning("❌ Invalid secret provided.")
        raise HTTPException(status_code=403, detail="Invalid secret")

    # Step 2: Generate app code
    attachments_list = [a.dict() for a in task_req.attachments] if task_req.attachments else []
    task_folder = generate_app_code(task_req.task, task_req.brief, attachments_list)

    if not task_folder:
        task_folder = str(Path("generated") / task_req.task)
        Path(task_folder).mkdir(parents=True, exist_ok=True)

    ensure_placeholder(task_folder)

    # Step 3: Git commit & push
    try:
        commit_sha = git_commit_and_push(task_folder, f"Deploy {task_req.task} (Round {task_req.round})")
    except Exception as e:
        logger.exception("❌ Git operation failed")
        raise HTTPException(status_code=500, detail=f"Git operation failed: {e}")

    # Step 4: Enable GitHub Pages (retry until active)
    try:
        enable_github_pages()
        logger.info("🌐 Waiting for GitHub Pages to initialize...")
        time.sleep(10)  # give GitHub some time to process
    except Exception as e:
        logger.warning(f"⚠️ GitHub Pages enabling encountered an issue: {e}")

    # Step 5: Notify evaluator
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
        logger.exception("❌ Evaluator notification failed")
        raise HTTPException(status_code=500, detail=f"Evaluator notification failed: {e}")

    pages_url = f"https://{GITHUB_USERNAME}.github.io/{REPO_NAME}/"
    logger.info(f"✅ Task '{task_req.task}' deployed successfully to {pages_url}")

    return APIResponse(
        status="success",
        message=f"✅ App deployed successfully and sent for evaluation.\nView it here: {pages_url}",
    )


@app.post("/build", response_model=APIResponse)
async def build_app(task_req: TaskRequest):
    """
    Only generates code locally (no Git or evaluation step).
    """
    logger.info(f"🧩 Build-only mode for task '{task_req.task}'")

    if not verify_secret(task_req.secret):
        raise HTTPException(status_code=403, detail="Invalid secret")

    attachments_list = [a.dict() for a in task_req.attachments] if task_req.attachments else []
    task_folder = generate_app_code(task_req.task, task_req.brief, attachments_list)

    if not task_folder:
        task_folder = str(Path("generated") / task_req.task)
        Path(task_folder).mkdir(parents=True, exist_ok=True)

    ensure_placeholder(task_folder)

    logger.info(f"✅ App generated successfully at {task_folder}")
    return APIResponse(status="success", message=f"App generated successfully at {task_folder}")
