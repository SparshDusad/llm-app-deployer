from fastapi import FastAPI, Request, HTTPException
from models import TaskRequest, APIResponse
from utils.verifier import verify_secret
from utils.logger import get_logger

app = FastAPI(title="LLM Code Deployment API")
logger = get_logger(__name__)

@app.post("/api-endpoint", response_model=APIResponse)
async def receive_task(request: TaskRequest):
    # Step 1: Verify secret
    if not verify_secret(request.secret):
        logger.warning(f"Invalid secret from {request.email}")
        raise HTTPException(status_code=403, detail="Invalid secret")

    # Step 2: Log task info
    logger.info(f"✅ Task received from {request.email}: {request.task} (Round {request.round})")

    # Step 3: Send confirmation
    return APIResponse(
        status="success",
        message=f"Task {request.task} (round {request.round}) received and verified."
    )
