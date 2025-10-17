🚀 LLM App Deployer

This project is a fully automated pipeline that takes a high-level task brief, uses a Large Language Model (LLM) to generate a complete web application, and deploys it directly to GitHub Pages. It's designed to go from idea to live deployment with a single API call.

📘 Summary

The core goal of this project is to automate the entire lifecycle of an AI-assisted application — from code generation to live deployment and evaluation — with zero manual intervention.

Features

API-Driven: Accepts a JSON POST request to kick off the entire process.

LLM Code Generation: Uses Google's Gemini model to generate HTML, CSS, and JavaScript code based on a task brief.

Automated Git Operations: Automatically commits and pushes the generated code to a dedicated subfolder in this repository.

GitHub Pages Deployment: Programmatically enables and manages GitHub Pages deployment for the repository.

Evaluation Notification: Sends the final deployment details (repo URL, live Pages URL, commit SHA) to a specified evaluation endpoint.

⚙️ Setup Instructions

Follow these steps to get the project running on your local machine.

1. Clone the Repository

git clone [https://github.com/SparshDusad/llm-app-deployer.git](https://github.com/SparshDusad/llm-app-deployer.git)
cd llm-app-deployer


2. Create and Activate a Virtual Environment

# For macOS/Linux
python3 -m venv venv
source venv/bin/activate

# For Windows
python -m venv venv
venv\Scripts\activate


3. Install Dependencies

Install all required Python packages from the requirements.txt file.

pip install -r requirements.txt


4. Configure Environment Variables

Create a file named .env in the root of the project and add the following variables. This file is included in .gitignore to keep your secrets safe.

# Your GitHub Username
GITHUB_USERNAME="YourGitHubUsername"

# Your GitHub Personal Access Token (with 'repo' scope)
GITHUB_TOKEN="ghp_YourTokenHere"

# The name of the repository you are deploying to
REPO_NAME="llm-app-deployer"

# Your Google API Key for the Gemini LLM
GOOGLE_API_KEY="YourGoogleApiKeyHere"

# A secret key to protect your API endpoint
API_SECRET_KEY="ChooseAStrongSecretPassword"


▶️ Usage

1. Run the FastAPI Server

Start the application server using Uvicorn. The --reload flag will automatically restart the server when you make code changes.

uvicorn main:app --reload


The API will now be running at http://127.0.0.1:8000.

2. Call the API Endpoint

You can trigger the deployment process by sending a POST request to the /api-endpoint. You can use a tool like Postman or the curl command below.

curl -X POST [http://127.0.0.1:8000/api-endpoint](http://127.0.0.1:8000/api-endpoint) \
  -H "Content-Type: application/json" \
  -d '{
    "secret": "ChooseAStrongSecretPassword",
    "email": "student@example.com",
    "task": "your-unique-task-name",
    "brief": "Create a simple web app that converts temperature from Celsius to Fahrenheit.",
    "round": 1,
    "nonce": "some_random_string_123",
    "evaluation_url": "[https://httpbin.org/post](https://httpbin.org/post)"
  }'


3. Check the Output

If successful, the API will return a 200 OK response with a JSON body similar to this:

{
  "status": "success",
  "message": "✅ App deployed successfully. View it here: [https://YourGitHubUsername.github.io/llm-app-deployer/generated/your-unique-task-name/](https://YourGitHubUsername.github.io/llm-app-deployer/generated/your-unique-task-name/)"
}


You can then check the provided URL to see your live application. Note that it may take GitHub Pages 1-2 minutes to build and serve the new site.

🧩 Code Explanation


Key Modules

main.py: The entry point of the application. It defines the /api-endpoint and orchestrates the entire workflow by calling the various helper modules.

utils/git_helper.py: This is the core of the automation.

git_commit_and_push(): A robust function that handles git configuration, checking out the correct branch, forcefully adding the generated files, committing them, and pushing to the remote repository. It is designed to work reliably in a server environment like Render.

enable_github_pages(): Uses the GitHub REST API to programmatically enable GitHub Pages for the repository if it's not already active.

utils/builder_agent.py (Assumed): This module contains the logic for formatting the prompt and calling the Google Gemini API to generate the application code.

🪪 License

This project is licensed under the MIT License. See the LICENSE file for more details.
