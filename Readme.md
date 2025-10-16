🚀 LLM Code Deployment Project

This project automates the build, deployment, and evaluation of a web application using a Large Language Model (LLM). It takes a task brief, generates the necessary code, deploys the app to GitHub Pages, and notifies an evaluation API with the deployment details.

📘 Summary

Goal: To create a zero-touch pipeline that handles the full lifecycle of an AI-assisted application—from code generation to final deployment and evaluation.

Features:

✅ Request Handling: Receives and validates application build requests via a FastAPI endpoint.

⚙️ Code Generation: Automatically generates web application code using the Gemini LLM.

📤 Automated Deployment: Pushes the generated code to a GitHub repository and deploys it to GitHub Pages.

🔍 Evaluation: Notifies an external API with commit and deployment details for validation.

🧠 Robust Logging: Logs all steps and handles errors with clear, informative messages.

📝 Description

This project serves as a complete, end-to-end solution for automated software deployment powered by a Large Language Model. The core of the system is a FastAPI backend that listens for incoming POST requests containing a task brief.

When a valid request is received, the workflow is as follows:

Code Generation: The application forwards the task brief to the Google Gemini API, which generates the complete HTML, CSS, and JavaScript code for a functional web application.

File System Integration: The generated code is saved into a local generated/ directory within the project structure.

Version Control & Deployment: A helper script takes over, programmatically forcing the addition of the new files to a Git commit. It then pushes this commit to a designated GitHub repository.

Live on the Web: The push to the main branch automatically triggers a GitHub Pages deployment, making the new web application live.

Evaluation: Finally, the system sends a POST request to a specified evaluation URL, providing the repository link, commit SHA, and live page URL to confirm a successful deployment cycle.

⚙️ Setup Instructions

1. Clone the Repository

git clone [https://github.com/](https://github.com/)<your-username>/<repo-name>.git
cd <repo-name>


2. Create a Virtual Environment

# For macOS/Linux
python3 -m venv venv
source venv/bin/activate

# For Windows
python -m venv venv
.\venv\Scripts\activate


3. Install Dependencies

pip install -r requirements.txt


4. Configure Environment Variables

Create a .env file in the project root and add the following required variables. These are essential for authentication and API communication.

GITHUB_USERNAME="your-github-username"
GITHUB_TOKEN="your-personal-access-token"
GOOGLE_API_KEY="your-gemini-api-key"
API_SECRET_KEY="a-secret-password-you-create"
REPO_NAME="the-name-of-your-github-repo"


▶️ Usage

Once the setup is complete, you can run the FastAPI server:

uvicorn main:app --reload


The application will be running locally. You can send POST requests to its endpoints (e.g., /api-endpoint) to trigger the build and deployment process.

The script will:

Build the app using the LLM.

Deploy the generated site to GitHub Pages.

Send the repository and commit details to the evaluation API.

🧩 Code Explanation

Key Files

main.py: The main FastAPI application that exposes the API endpoints and orchestrates the entire workflow.

builder_agent.py: Contains the logic for interacting with the Gemini LLM to generate application code.

utils/git_helper.py: A robust script to handle all Git operations, including adding, committing, and pushing code to GitHub.

utils/evaluator.py: Sends the final deployment details (repo URL, commit SHA) to the external evaluation API.

utils/logger.py: Configures structured, clear logging for easier debugging.

🪪 License

This project is licensed under the MIT License. See the LICENSE file for more details.