import subprocess
import os
import shutil
import requests
import json
import time  # Import the time module
from datetime import datetime  # Import the datetime module

from dotenv import load_dotenv

import google.generativeai as genai

load_dotenv()

MODEL = os.environ.get("MODEL", "gemini")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")

def call_gemini_api(prompt):
    """Calls the Gemini API with the given prompt."""
    log_to_file(f"Gemini API Prompt:\n{prompt}") #Log Prompt to File
    if not GEMINI_API_KEY:
        raise ValueError("GEMINI_API_KEY environment variable not set. MODEL contains gemini, but no API key provided.")

    genai.configure(api_key=GEMINI_API_KEY)

    model = genai.GenerativeModel('gemini-1.5-flash')  # Use Gemini 2.0 Flash

    try:
        response = model.generate_content(prompt)
        response_text = response.text  # Extract the text from the response
        log_to_file(f"Gemini API Response:\n{response_text}")  #Log response to file
        return response_text
    except Exception as e:
        print(f"Error calling Gemini API: {e}")
        return None

def generate_response(prompt, max_tokens=1000):
    """Generates a response based on the configured model (Gemini)."""
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

def log_to_file(content):
    """Logs the given content to a file with a timestamp."""
    log_file_path = "/app/data/log.txt"  # Path to the log file
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


def get_ai_solution(error_message, commands, repo_url):
    """Sends the error message, commands, and repo URL to Gemini and returns the response."""
    prompt = f"""You are a Docker expert. The following error occurred while trying to build a Docker Compose project:

    Error Message:
    {error_message}

    Commands Executed:
    {commands}

    Git Repository:
    {repo_url}

    Provide a concise explanation of the error and suggest a fix.  Format your response as a markdown code block with the corrected commands or Dockerfile snippets, if applicable. If the error is environment-related or permission related, consider asking for Docker version or `whoami` inside the container.
    """

    #data = {   # Remove unneeded code
    #    "prompt": prompt,
    #    "model": MODEL,  # Use the MODEL environment variable
    #    "stream": False
    #}

    #log_to_file(f"Ollama Prompt:\n{prompt}")  # Remove OLLAMA specific logs

    response = generate_response(prompt)

def main():
    """Main function to execute the commands, handle errors, and interact with Gemini."""

    rotate_log_file()  # Rotate the log file before each execution
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
