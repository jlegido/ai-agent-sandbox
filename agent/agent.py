import subprocess
import os
import shutil
import re  # Import the regular expression module
from datetime import datetime

from dotenv import load_dotenv
import google.generativeai as genai

load_dotenv()

MODEL = os.environ.get("MODEL", "gemini")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")

def call_gemini_api(prompt):
    """Calls the Gemini API with the given prompt."""
    log_to_file(f"Gemini API Prompt:\n{prompt}")
    if not GEMINI_API_KEY:
        raise ValueError("GEMINI_API_KEY environment variable not set. MODEL contains gemini, but no API key provided.")

    genai.configure(api_key=GEMINI_API_KEY)
    model = genai.GenerativeModel('gemini-1.5-flash')

    try:
        response = model.generate_content(prompt)
        response_text = response.text
        log_to_file(f"Gemini API Response:\n{response_text}")
        return response_text
    except Exception as e:
        print(f"Error calling Gemini API: {e}")
        return None

def generate_response(prompt):
    """Generates a response using the configured model (Gemini)."""
    if "gemini" in MODEL.lower():
        response = call_gemini_api(prompt)
        if response:
            return response
        else:
            return "Error: Failed to generate response from Gemini API."
    else:
        return "Error: Gemini API not enabled. Set MODEL environment variable to include 'gemini'."

def execute_commands(commands):
    """Executes a list of shell commands and returns the output and error."""
    print(f"Executing commands:\n{commands}")
    try:
        process = subprocess.run(
            commands,
            shell=True,
            cwd="/tmp",
            capture_output=True,
            text=True,
            check=True  # Raise an exception if the command fails
        )
        print(f"Commands executed successfully.")
        return process.stdout, process.stderr
    except subprocess.CalledProcessError as e:
        print(f"Commands failed with error:")
        return e.stdout, e.stderr  # Capture stdout even on error

def extract_code(text):
    """Extracts code blocks from a markdown-formatted text."""
    code_blocks = re.findall(r"```(?:\w+)?\n(.*?)\n```", text, re.DOTALL)
    return code_blocks

def cleanup():
    """Removes the ai-agent-wordpress directory if it exists."""
    try:
        repo_dir = "/tmp/ai-agent-wordpress"
        if os.path.exists(repo_dir):
            shutil.rmtree(repo_dir)
            print(f"Successfully removed {repo_dir}")
    except Exception as e:
        print(f"Error during cleanup: {e}")

def log_to_file(content):
    """Logs the given content to a file with a timestamp."""
    log_file_path = "/app/data/log.txt"
    try:
        with open(log_file_path, "a") as log_file:
            log_file.write(f"{datetime.now()} - {content}\n")
    except Exception as e:
        print(f"Error writing to log file: {e}")

def rotate_log_file():
    """Rotates the log file by renaming it with a timestamp."""
    log_file_path = "/app/data/log.txt"
    try:
        if os.path.exists(log_file_path):
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            new_log_file_name = f"{log_file_path}.{timestamp}"
            os.rename(log_file_path, new_log_file_name)
            print(f"Rotated log file to: {new_log_file_name}")
    except Exception as e:
        print(f"Error rotating log file: {e}")

def get_ai_solution(error_message, commands, repo_url, attempt=1):
    """Sends the error message, commands, and repo URL to Gemini and returns the response."""
    prompt = f"""You are a Docker expert.  This is attempt {attempt} to solve the problem. The following error occurred while trying to build a Docker Compose project:

    Error Message:
    {error_message}

    Commands Executed (Previous Attempt):
    {commands}

    Git Repository:
    {repo_url}

    Provide a concise explanation of the error and suggest a fix. Format your response as a markdown code block with the corrected commands or Dockerfile snippets. Only provide a full code example.
    """

    response = generate_response(prompt)
    return response

def main():
    """Main function to execute the commands, handle errors, and interact with Gemini."""

    rotate_log_file()
    cleanup()

    repo_url = "https://github.com/jlegido/ai-agent-wordpress"
    initial_commands = """
    cd /tmp
    rm -fr ai-agent-wordpress
    git clone https://github.com/jlegido/ai-agent-wordpress
    cd ai-agent-wordpress
    docker compose build
    """

    commands = initial_commands  # Start with initial commands
    stderr = "No Error"  # Initialize

    attempt = 1  # Attempt number

    while "Error" in stderr and attempt <= 3: # Limited to 3 attempts
        print(f"Attempt {attempt}:")
        stdout, stderr = execute_commands(commands)

        if stderr:
            print("Error output:")
            print(stderr)

            ai_solution = get_ai_solution(stderr, commands, repo_url, attempt) # Send attempt number
            print("AI Response:", ai_solution)

            code_blocks = extract_code(ai_solution)
            if code_blocks:
                commands = code_blocks[0]  # Use the first code block as commands
                print(f"Extracted commands:\n{commands}")
            else:
                print("No code block found in AI response.  Stopping.")
                break  # Stop if no code is found.

        else:
            print("Command execution successful!")
            print("Standard output:")
            print(stdout)
            break  # Exit loop if successful

        attempt += 1

    cleanup()

if __name__ == "__main__":
    main()
