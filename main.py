from fastapi import FastAPI, Request, HTTPException
from models import TaskRequest, APIResponse
from utils.verifier import verify_secret
from utils.logger import get_logger
from builder_agent import generate_app_code

app = FastAPI(title="LLM Code Deployment API")
logger = get_logger(__name__)


@app.post("/api-endpoint", response_model=APIResponse)
async def receive_task(request: TaskRequest):
    # Verify secret
    if not verify_secret(request.secret):
        logger.warning(f"Invalid secret from {request.email}")
        raise HTTPException(status_code=403, detail="Invalid secret")

    logger.info(f"✅ Task received from {request.email}: {request.task} (Round {request.round})")

    # Phase 2: generate app code
    output_path = generate_app_code(request.task, request.brief, [a.dict() for a in request.attachments])

    return APIResponse(
        status="success",
        message=f"Task {request.task} (round {request.round}) received, code generated at {output_path}."
    )
