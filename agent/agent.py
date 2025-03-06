import requests
import os

OLLAMA_URL = "http://ollama:11434/api/generate"
LOG_FILE = "/app/data/log.txt"  # This will be stored in the Docker volume

def ask_ollama(prompt):
    """Send a question to Ollama and return the response."""
    payload = {
        "model": "llama3.2-vision",
        "prompt": prompt,
        "stream": False
    }

    response = requests.post(OLLAMA_URL, json=payload)
    response_data = response.json()
    return response_data.get("response", "No response received")

def log_conversation(question, answer):
    """Write question and answer to a log file."""
    with open(LOG_FILE, "a") as f:
        f.write(f"Q: {question}\nA: {answer}\n{'-'*40}\n")

def main():
    question = "What is the capital of France?"
    answer = ask_ollama(question)
    
    log_conversation(question, answer)
    print(f"Logged: {question} -> {answer}")

if __name__ == "__main__":
    main()

