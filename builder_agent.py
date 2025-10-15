import os
import re
from pathlib import Path
from utils.logger import get_logger
import google.generativeai as genai
from dotenv import load_dotenv

logger = get_logger(__name__)
load_dotenv()
# --- Step 1: Configure the API Key ---
try:
    GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
    if not GOOGLE_API_KEY:
        raise ValueError("GOOGLE_API_KEY environment variable not set.")
    genai.configure(api_key=GOOGLE_API_KEY)
    
    # --- Step 2: Create the Model Instance (after configuration) ---
    # Use a modern, recommended model.
    model = genai.GenerativeModel('gemini-2.5-flash')

except Exception as e:
    logger.error(f"Error during Gemini initialization: {e}")
    # Set model to None if initialization fails, so the app doesn't crash
    model = None

def generate_app_code(task: str, brief: str, attachments: list = None) -> str:
    """
    Generate minimal web app code (HTML/CSS/JS) from a brief using Gemini.
    Returns the path to the generated folder.
    """
    # Check if the model failed to initialize
    if not model:
        logger.error("Gemini model is not available. Cannot generate code.")
        return ""

    # Ensure attachments is not None
    attachments = attachments or []

    # Directory for generated app
    output_dir = Path("generated") / task
    output_dir.mkdir(parents=True, exist_ok=True)

    # Prepare prompt
    attachment_info = "\n".join([f"{a['name']}: {a['url']}" for a in attachments])
    prompt = f"""
    You are an expert web developer.
    Task: {task}
    Brief: {brief}
    Attachments: {attachment_info if attachment_info else 'None'}
    
    Generate minimal working HTML, CSS, and JS files. Your response MUST contain exactly three code blocks: one for HTML, one for CSS, and one for JavaScript.
    The HTML code must be in a ```html block.
    The CSS code must be in a ```css block.
    The JavaScript code must be in a ```js block.
    
    The final output should be ONLY the code blocks. Do not add any other explanatory text around them.
    """

    logger.info(f"Generating code for task: {task} using Gemini...")
    
    try:
        # --- Step 3: Call the Model (use the single, pre-configured instance) ---
        config = genai.GenerationConfig(temperature=0.3)
        response = model.generate_content(prompt, generation_config=config)
        
        # Extract generated code from Gemini's response structure
        code_text = response.text
        
    except Exception as e:
        logger.error(f"Failed to generate code with Gemini: {e}")
        return "" # Return empty string on failure

    # Simple parsing: split by ```html, ```css, ```js
    def extract_code(text, lang):
        pattern = f"```{lang}\\s*(.*?)```"
        match = re.search(pattern, text, re.DOTALL)
        return match.group(1).strip() if match else ""

    # Provide better fallbacks if a block is missing
    html_code = extract_code(code_text, "html") or "<!-- Gemini did not return valid HTML -->"
    css_code = extract_code(code_text, "css") or "/* Gemini did not return valid CSS */"
    js_code = extract_code(code_text, "js") or "// Gemini did not return valid JS"

    # Write files
    (output_dir / "index.html").write_text(html_code)
    (output_dir / "style.css").write_text(css_code)
    (output_dir / "script.js").write_text(js_code)

    logger.info(f"Generated files at: {output_dir.resolve()}")
    return str(output_dir.resolve())
