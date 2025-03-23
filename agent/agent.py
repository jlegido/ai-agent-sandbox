import subprocess
import os
import shutil
import re  # Import the regular expression module
from datetime import datetime

from dotenv import load_dotenv
import google.generativeai as genai
import shlex # Import shlex for safer command execution

load_dotenv()

'''
COMMAND = """
cd /tmp
rm -fr ai-agent-wordpress
git clone https://github.com/jlegido/ai-agent-wordpress
cd ai-agent-wordpress
docker compose build
"""
'''

class Agent:
    """
    An intelligent agent that executes commands, interacts with the Gemini API,
    and handles errors.
    """

    def __init__(self, command="", max_attempts=3, model="gemini"):
        """
        Initializes the Agent.

        Args:
            command (str): The initial command to execute.
            max_attempts (int): The maximum number of attempts to execute the command.
            model (str): The name of the language model to use (default: "gemini").
        """
        self.command = os.environ.get("COMMAND")
        self.max_attempts = int(os.environ.get("MAX_ATTEMPTS"))
        self.model = os.environ.get("MODEL")
        self.gemini_api_key = os.environ.get("GEMINI_API_KEY")
        self.output_history = []  # Store command output history
        self.log_file_path = "/app/data/log.txt" #Define a LogFile

    def call_gemini_api(self, prompt):
        """Calls the Gemini API with the given prompt."""
        self.log_to_file(f"Gemini API Prompt:\n{prompt}")
        if not self.gemini_api_key:
            raise ValueError(
                "GEMINI_API_KEY environment variable not set. MODEL contains gemini, but no API key provided."
            )

        genai.configure(api_key=self.gemini_api_key)
        model = genai.GenerativeModel("gemini-1.5-flash")

        try:
            response = model.generate_content(prompt)
            response_text = response.text
            self.log_to_file(f"Gemini API Response:\n{response_text}")
            return response_text
        except Exception as e:
            print(f"Error calling Gemini API: {e}")
            return None

    def generate_response(self, prompt):
        """Generates a response using the configured model (Gemini)."""
        if "gemini" in self.model.lower():
            response = self.call_gemini_api(prompt)
            if response:
                return response
            else:
                return "Error: Failed to generate response from Gemini API."
        else:
            return "Error: Gemini API not enabled. Set MODEL environment variable to include 'gemini'."

    def execute_command(self, command):
        """Executes a shell command and captures stdout and stderr."""
        print(f"Executing command:\n{command}")

        try:
            # Use shlex.split to handle spaces and quotes correctly
            command_list = shlex.split(command)
            result = subprocess.run(command_list, capture_output=True, text=True, check=False) #Added Check=False
            stdout = result.stdout.strip()
            stderr = result.stderr.strip()

            # Log the return code
            return_code = result.returncode
            print(f"Command finished with return code: {return_code}") #added for debugging
            
        except FileNotFoundError as e:
            # Handle cases where the command is not found
            stdout = ""
            stderr = f"FileNotFoundError: {e}. The command '{command}' could not be found."
            return_code = 127 # Standard code for "command not found"
        except Exception as e:
            # Handle other potential exceptions during command execution
            stdout = ""
            stderr = f"An unexpected error occurred while executing the command: {e}"
            return_code = 1 # Generic error code
            
        # Store outputs in memory
        output_entry = {"command": command, "stdout": stdout, "stderr": stderr, "return_code": return_code}
        self.output_history.append(output_entry)
        
        return stdout, stderr

    def log_to_file(self, content):
        """Logs the given content to a file with a timestamp."""
        try:
            with open(self.log_file_path, "a") as log_file:
                log_file.write(f"{datetime.now()} - {content}\n")
        except Exception as e:
            print(f"Error writing to log file: {e}")

    def rotate_log_file(self):
        """Rotates the log file by renaming it with a timestamp."""
        try:
            if os.path.exists(self.log_file_path):
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                new_log_file_name = f"{self.log_file_path}.{timestamp}"
                os.rename(self.log_file_path, new_log_file_name)
                print(f"Rotated log file to: {new_log_file_name}")
        except Exception as e:
            print(f"Error rotating log file: {e}")

    def get_success(self, command: str, stdout: str, stderr: str) -> bool:
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
        response = self.generate_response(prompt)
        if "success" in response:
            return True
        return False

    def create_prompt(self, user_input):
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
            for i, entry in enumerate(self.output_history)  # Include all attempts
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

    def extract_code(self, text):
        """Extracts shell commands from a markdown-formatted text."""
        prompt = f"""You are an AI assistant that extracts command-line commands from a given response.  
The response may contain markdown-formatted code blocks.  

Extract all command-line commands enclosed in triple backticks (```bash, ```sh, or ``` without a language specifier).  
Return only the extracted commands as a list, without explanations or formatting.  

LLM Response:  
{text}
"""

        response = self.generate_response(prompt)
        return response

    def run(self):
        """
        Main function to execute the commands, handle errors, and interact with Gemini.
        """
        self.rotate_log_file()
        attempt = 1
        is_success = False

        while not is_success and attempt <= self.max_attempts:
            print(f"attempt {attempt}:")
            print(f"command {self.command}")
            stdout, stderr = self.execute_command(self.command)
            attempt += 1

            is_success = self.get_success(self.command, stdout, stderr)

            prompt = self.create_prompt(self.command)
            print("---------------------------------- PROMPT -----------------------------------------------------------------------")
            print(f"{prompt}")

            response = self.generate_response(prompt)
            print("--------------------------------- RESPONSE -----------------------------------------------------------------")
            print(f"{response}")

            self.command = self.extract_code(response)
            print("-------------------------- COMMAND -------------------------------------------------------------------------")
            print(f"{self.command}")

def extract_code_no_llm(text):
    """Extracts shell commands from markdown-formatted text (without LLM)."""
    command_blocks = re.findall(r"```(?:bash|sh)?\n(.*?)\n```", text, re.DOTALL)
    return command_blocks

if __name__ == "__main__":
    #agent = Agent(command=COMMAND)
    agent = Agent()
    agent.run()
