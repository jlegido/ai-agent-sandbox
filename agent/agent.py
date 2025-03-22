import subprocess
import os
import shutil
import requests
import json
import time  # Import the time module

from dotenv import load_dotenv

load_dotenv()

OLLAMA_URL = os.getenv("OLLAMA_URL", "http://ollama:11434/api/generate")  # Default Ollama URL
MODEL = os.getenv("MODEL", "deepseek-coder")  # Get the MODEL environment variable
MAX_RETRIES = 3
RETRY_DELAY = 2  # seconds

def execute_commands(commands):
    """Executes a list of shell commands and returns the output and error."""
    print(f"Executing commands:\n{commands}")  # Print commands to stdout BEFORE execution
    try:
        process = subprocess.run(
            commands,
            shell=True,
            cwd="/tmp",  # Run commands in /tmp
            capture_output=True,
            text=True,
            check=True  # Raise an exception if the command fails
        )
        print(f"Commands executed successfully.")  # Print success message
        return process.stdout, process.stderr
    except subprocess.CalledProcessError as e:
        print(f"Commands failed with error:")  # Print failure message
        return e.output, e.stderr

def cleanup():
    """Removes the ai-agent-wordpress directory if it exists."""
    try:
        repo_dir = "/tmp/ai-agent-wordpress"
        if os.path.exists(repo_dir):
            shutil.rmtree(repo_dir)
            print(f"Successfully removed {repo_dir}")
    except Exception as e:
        print(f"Error during cleanup: {e}")

def get_ai_solution(error_message, commands, repo_url):
    """Sends the error message, commands, and repo URL to Ollama and returns the response with retry logic."""
    prompt = f"""You are a Docker expert. The following error occurred while trying to build a Docker Compose project:

    Error Message:
    {error_message}

    Commands Executed:
    {commands}

    Git Repository:
    {repo_url}

    Provide a concise explanation of the error and suggest a fix.  Format your response as a markdown code block with the corrected commands or Dockerfile snippets, if applicable. If the error is environment-related or permission related, consider asking for Docker version or `whoami` inside the container.
    """

    data = {
        "prompt": prompt,
        "model": MODEL,  # Use the MODEL environment variable
        "stream": False
    }

    for attempt in range(MAX_RETRIES):
        try:
            response = requests.post(OLLAMA_URL, data=json.dumps(data), stream=False)
            response.raise_for_status()  # Raise HTTPError for bad responses (4xx or 5xx)
            json_response = response.json()
            ai_solution = json_response.get("response", "No response from AI.")

            return ai_solution

        except requests.exceptions.RequestException as e:
            print(f"Attempt {attempt + 1}/{MAX_RETRIES}: Error communicating with Ollama: {e}")
            if attempt < MAX_RETRIES - 1:
                time.sleep(RETRY_DELAY)  # Wait before retrying
            else:
                print("Max retries reached.  Returning error message.")
                return "Error communicating with AI after multiple retries. Check Ollama is running and accessible."
        except json.JSONDecodeError:
            return "Unexpected error occurred during JSON decoding."

        return "Unexpected error occurred."

def main():
    """Main function to execute the commands, handle errors, and interact with Ollama."""

    cleanup()

    commands = """
    cd /tmp
    rm -fr ai-agent-wordpress
    git clone https://github.com/jlegido/ai-agent-wordpress
    cd ai-agent-wordpress
    docker compose build
    """
    print(f"Executing commands:\n{commands}")  #Print current command to stdout

    stdout, stderr = execute_commands(commands)

    if stderr:
        print("Error output:")
        print(stderr)

        ai_solution = get_ai_solution(stderr, commands, "https://github.com/jlegido/ai-agent-wordpress")
        print("AI Response:", ai_solution)

    else:
        print("Command execution successful!")
        print("Standard output:")
        print(stdout)

    cleanup()

if __name__ == "__main__":
    main()
