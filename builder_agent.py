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


def generate_readme_fallback(brief: str, attachments: list, task: str, round_num: int = 1) -> str:
    """Fallback README if LLM doesn't provide one."""
    attachments_list = "\n".join([f"- {a['name']}: {a['url']}" for a in attachments]) or "None"
    return f"""# {task}

## Summary
Automatically generated minimal web app for Round {round_num}.

## Brief
{brief}

## Setup
1. Clone the repo.
2. Open `index.html` in a browser.

## Usage
- View the HTML/CSS/JS locally.
- Attachments: {attachments_list}

## Files
- `index.html` – main HTML
- `style.css` – styles
- `script.js` – JavaScript
- `README.md` – this file

## License
MIT License
"""


def generate_app_code(task: str, brief: str, attachments: list = None, round_num: int = 1) -> dict:
    """
    Generate minimal web app (HTML/CSS/JS) + README.md from brief using Gemini.
    Returns a dict with `files` and `attachments`.
    """
    if not model:
        logger.error("Gemini model unavailable. Cannot generate code.")
        return {}

    attachments = attachments or []
    output_dir = Path("generated") / task
    output_dir.mkdir(parents=True, exist_ok=True)

    attachment_info = "\n".join([f"{a['name']}: {a['url']}" for a in attachments])
    prompt = f"""
    You are an expert frontend developer.
    Task: {task}
    Brief: {brief}
    Attachments: {attachment_info or 'None'}

    Generate minimal working HTML, CSS, JS, and README.md.
    Response must contain code blocks:
    - ```html``` for HTML
    - ```css``` for CSS
    - ```js``` for JS
    - ```markdown``` for README.md (optional)
    Only include code blocks, no extra text.
    """

    logger.info(f"Generating code for task: {task}")

    try:
        config = genai.GenerationConfig(temperature=0.3)
        response = model.generate_content(prompt, generation_config=config)
        text = response.text
    except Exception as e:
        logger.error(f"Failed to generate code: {e}")
        return {}

    def extract_code(text, lang):
        pattern = f"```{lang}\\s*(.*?)```"
        match = re.search(pattern, text, re.DOTALL)
        return match.group(1).strip() if match else ""

    html_code = extract_code(text, "html") or "<!-- Missing HTML -->"
    css_code = extract_code(text, "css") or "/* Missing CSS */"
    js_code = extract_code(text, "js") or "// Missing JS"
    readme_code = extract_code(text, "markdown") or generate_readme_fallback(brief, attachments, task, round_num)

    # Save to folder
    (output_dir / "index.html").write_text(html_code)
    (output_dir / "style.css").write_text(css_code)
    (output_dir / "script.js").write_text(js_code)
    (output_dir / "README.md").write_text(readme_code)

    logger.info(f"Generated app + README at: {output_dir.resolve()}")

    return {
        "files": {
            "index.html": html_code,
            "style.css": css_code,
            "script.js": js_code,
            "README.md": readme_code
        },
        "attachments": attachments
    }


def update_app_code(task: str, brief: str, attachments: list = None, round_num: int = 2) -> dict:
    """
    Update existing app files (HTML/CSS/JS) + README.md based on a new brief.
    Returns dict with `files` and `attachments`.
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

    The folder contains index.html, style.css, script.js, README.md.
    Update code to match the new brief.
    Response must contain code blocks:
    - ```html``` full updated HTML
    - ```css``` full updated CSS
    - ```js``` full updated JS
    - ```markdown``` updated README.md (optional)
    Only include code blocks, no extra text.
    """

    logger.info(f"Updating app for task: {task}, Round {round_num}")

    try:
        config = genai.GenerationConfig(temperature=0.3)
        response = model.generate_content(prompt, generation_config=config)
        text = response.text
    except Exception as e:
        logger.error(f"Failed to update code: {e}")
        return {}

    def extract_code(text, lang):
        pattern = f"```{lang}\\s*(.*?)```"
        match = re.search(pattern, text, re.DOTALL)
        return match.group(1).strip() if match else ""

    html_code = extract_code(text, "html") or (output_dir / "index.html").read_text()
    css_code = extract_code(text, "css") or (output_dir / "style.css").read_text()
    js_code = extract_code(text, "js") or (output_dir / "script.js").read_text()
    readme_code = extract_code(text, "markdown") or generate_readme_fallback(brief, attachments, task, round_num)

    # Write updated files
    (output_dir / "index.html").write_text(html_code)
    (output_dir / "style.css").write_text(css_code)
    (output_dir / "script.js").write_text(js_code)
    (output_dir / "README.md").write_text(readme_code)

    # Log the update
    with open(output_dir / "update_log.txt", "a", encoding="utf-8") as f:
        f.write(f"Updated for Round {round_num} with new brief: {brief}\n")

    logger.info(f"App + README updated successfully at: {output_dir.resolve()}")

    return {
        "files": {
            "index.html": html_code,
            "style.css": css_code,
            "script.js": js_code,
            "README.md": readme_code
        },
        "attachments": attachments
    }
