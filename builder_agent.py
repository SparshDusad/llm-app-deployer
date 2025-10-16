import os
import re
from pathlib import Path
from utils.logger import get_logger
import google.generativeai as genai
from dotenv import load_dotenv

logger = get_logger(__name__)
load_dotenv()

# --- Gemini configuration ---
try:
    GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
    if not GOOGLE_API_KEY:
        raise ValueError("GOOGLE_API_KEY environment variable not set.")
    genai.configure(api_key=GOOGLE_API_KEY)
    model = genai.GenerativeModel("gemini-2.5-flash")
except Exception as e:
    logger.error(f"Gemini initialization failed: {e}")
    model = None


def generate_app_code(task: str, brief: str, attachments: list = None) -> str:
    """
    Generate minimal web app (HTML/CSS/JS) from brief using Gemini.
    Returns path to generated folder.
    """
    if not model:
        logger.error("Gemini model unavailable. Cannot generate code.")
        return ""

    attachments = attachments or []
    output_dir = Path("generated") / task
    output_dir.mkdir(parents=True, exist_ok=True)

    attachment_info = "\n".join([f"{a['name']}: {a['url']}" for a in attachments])
    prompt = f"""
    You are an expert frontend developer.
    Task: {task}
    Brief: {brief}
    Attachments: {attachment_info or 'None'}

    Generate minimal working HTML, CSS, and JS.
    Response must contain exactly three code blocks:
    - ```html``` for HTML
    - ```css``` for CSS
    - ```js``` for JS
    Only include code blocks, no extra text.
    """

    logger.info(f"Generating code for task: {task}")

    try:
        config = genai.GenerationConfig(temperature=0.3)
        response = model.generate_content(prompt, generation_config=config)
        code_text = response.text
    except Exception as e:
        logger.error(f"Failed to generate code: {e}")
        return ""

    def extract_code(text, lang):
        pattern = f"```{lang}\\s*(.*?)```"
        match = re.search(pattern, text, re.DOTALL)
        return match.group(1).strip() if match else ""

    html_code = extract_code(code_text, "html") or "<!-- Missing HTML -->"
    css_code = extract_code(code_text, "css") or "/* Missing CSS */"
    js_code = extract_code(code_text, "js") or "// Missing JS"

    (output_dir / "index.html").write_text(html_code)
    (output_dir / "style.css").write_text(css_code)
    (output_dir / "script.js").write_text(js_code)

    logger.info(f"Generated app at: {output_dir.resolve()}")
    return str(output_dir.resolve())


def update_app_code(task: str, brief: str, attachments: list = None) -> str:
    """
    Update existing app files based on a new brief.
    """
    output_dir = Path("generated") / task
    if not output_dir.exists():
        raise FileNotFoundError(f"No app found for task '{task}'. Run build first.")

    attachments = attachments or []
    attachment_info = "\n".join([f"{a['name']}: {a['url']}" for a in attachments])

    prompt = f"""
    You are a senior frontend engineer updating an existing web app.
    Task: {task}
    New Brief: {brief}
    Attachments: {attachment_info or 'None'}

    The folder contains index.html, style.css, script.js.
    Update code to match the new brief.
    Response must contain exactly three code blocks:
    - ```html``` full updated HTML
    - ```css``` full updated CSS
    - ```js``` full updated JS
    """

    try:
        config = genai.GenerationConfig(temperature=0.3)
        response = model.generate_content(prompt, generation_config=config)
        code_text = response.text
    except Exception as e:
        logger.error(f"Failed to update code: {e}")
        return ""

    def extract_code(text, lang):
        pattern = f"```{lang}\\s*(.*?)```"
        match = re.search(pattern, text, re.DOTALL)
        return match.group(1).strip() if match else ""

    html_code = extract_code(code_text, "html") or "<!-- Update failed -->"
    css_code = extract_code(code_text, "css") or "/* Update failed */"
    js_code = extract_code(code_text, "js") or "// Update failed"

    (output_dir / "index.html").write_text(html_code)
    (output_dir / "style.css").write_text(css_code)
    (output_dir / "script.js").write_text(js_code)

    with open(output_dir / "update_log.txt", "a", encoding="utf-8") as f:
        f.write(f"Updated for new brief: {brief}\n")

    logger.info(f"App updated successfully at: {output_dir.resolve()}")
    return str(output_dir.resolve())
