import os
from dotenv import load_dotenv

load_dotenv()
SECRET_KEY = os.getenv("SECRET_KEY")

def verify_secret(secret: str) -> bool:
    """Compare provided secret with stored secret."""
    return secret == SECRET_KEY
