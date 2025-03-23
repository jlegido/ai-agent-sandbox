import subprocess
import os
import shutil
import re  # Import the regular expression module
from datetime import datetime

from dotenv import load_dotenv
import google.generativeai as genai

load_dotenv()

command = """
cd /tmp
rm -fr ai-agent-wordpress
git clone https://github.com/jlegido/ai-agent-wordpress
cd ai-agent-wordpress
docker compose build
"""
max_attempts=3

MODEL = os.environ.get("MODEL", "gemini")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")

# Store command output history
output_history = []

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

def execute_command(command):
    """Executes a shell command and captures stdout and stderr."""
    print(f"Executing command:\n{command}")
    result = subprocess.run(command, shell=True, capture_output=True, text=True)
    stdout = result.stdout.strip()
    stderr = result.stderr.strip()
    
    # Store outputs in memory
    output_entry = {"command": command, "stdout": stdout, "stderr": stderr}
    output_history.append(output_entry)
    
    return stdout, stderr

def extract_code(text):
    """Extracts code blocks from a markdown-formatted text."""
    code_blocks = re.findall(r"```(?:\w+)?\n(.*?)\n```", text, re.DOTALL)
    return code_blocks

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

def main():
    """main function to execute the commands, handle errors, and interact with gemini."""
    rotate_log_file()
    attempt = 1  # attempt number
    is_success = False

    while not is_success and attempt <= 3: # limited to 3 attempts
        print(f"attempt {attempt}:")
        stdout, stderr = execute_command(command)
        attempt += 1

        # TODO: ask LLM, based in stdout and stderr, if it was successful
        is_success = get_success(command, stdout, stderr)

def get_success(command: str, stdout: str, stderr: str) -> bool:
    """ask LLM, based in stdout and stderr, if it was successful"""
    prompt = f"""SYSTEM: Analyze the command execution results. Consider both stdout and stderr.
Respond with exactly one word: "success" or "error".

USER:
Command executed: {command}
---
STDOUT:
{stdout}
---
STDERR:
{stderr}
---
Analysis: Did this command execute successfully? Consider any error messages
or unexpected outputs in either stream. Respond only with "success" or "error"."""
    response = generate_response(prompt)
    if "success" in response:
        return True
    return False

def create_prompt(user_input):
    """Generates a structured debugging prompt with failure history."""
    system_message = """You are a senior software engineer. Analyze previous failed attempts and:
1. Identify the root cause of errors
2. Propose a corrected solution
3. Explain key changes briefly

Format response:
<analysis>
Root cause: [concise identification of main issue]
Critical error: [most relevant error excerpt]
</analysis>

<solution>
[corrected code using markdown format]
</solution>"""

    history_str = "\n\n".join([
        f"Attempt #{i+1}:\n"
        f"COMMAND: {entry['command']}\n"
        f"STDOUT: {entry['stdout'][-500:]}\n"  # Truncate long outputs
        f"STDERR: {entry['stderr'][-500:]}\n"
        f"{'-'*40}"
        for i, entry in enumerate(output_history[-3:])  # Last 3 attempts
    ])

    prompt = f"""## SYSTEM ROLE ##
{system_message}

## DEBUGGING HISTORY ##
{history_str or 'No previous attempts recorded'}

## CURRENT TASK ##
{user_input}

## REQUIREMENTS ##
1. Cross-verify against all previous errors
2. Maintain original functionality
3. Include validation steps
4. Output ONLY the formatted response template"""

    return prompt

def main():
    """main function to execute the commands, handle errors, and interact with gemini."""
    rotate_log_file()
    attempt = 1  # attempt number
    is_success = False

    while not is_success and attempt <= max_attempts: # limited to 3 attempts
        print(f"attempt {attempt}:")
        print(f"command {command}")
        stdout, stderr = execute_command(command)
        attempt += 1

        # TODO: ask LLM, based in stdout and stderr, if it was successful
        is_success = get_success(command, stdout, stderr)


        prompt = create_prompt(command)
        print(f"prompt {prompt}")

        response = generate_response(prompt)
        print(f"response {response}")
        
        # TODO: implement a function or a call to LLM to extract a command from LLM response

if __name__ == "__main__":
    main()
