import random
import requests
import time
from datetime import datetime

# Define the Ollama API endpoint
OLLAMA_API_URL = "http://ollama:11434/v1/chat/completions"

# Function to log the questions and answers into a file
def log_to_file(content):
    with open("/app/data/log.txt", "a") as log_file:
        log_file.write(f"{datetime.now()} - {content}\n")

# Function to get a response from Ollama
def get_ollama_response(prompt):
    headers = {
        "Content-Type": "application/json",
    }
    data = {
        "model": "llama3.2-vision",
        "messages": [{"role": "user", "content": prompt}],
    }

    try:
        response = requests.post(OLLAMA_API_URL, json=data, headers=headers)
        response.raise_for_status()  # Raise an error for bad responses (4xx or 5xx)
        return response.json()['choices'][0]['message']['content'].strip()
    except requests.exceptions.RequestException as e:
        log_to_file(f"Error communicating with Ollama: {str(e)}")
        return None

# Main function to start the guessing game
def main():
    # Generate a random number between 1 and 10
    secret_number = random.randint(1, 10)
    log_to_file(f"Secret number generated: {secret_number}")  # Log the secret number for debugging purposes


    # Ask Ollama to guess the number, only expect a number in response
    prompt = "Guess a number between 1 and 10. Reply only with the number."

    while True:
        log_to_file(f"Question: {prompt}")
        reply = get_ollama_response(prompt)
        if reply is None:
            log_to_file("Ollama failed to respond.")
            break

        log_to_file(f"Reply: {reply}")

        # Check if Ollama's guess is correct
        try:
            guess = int(reply)
            if guess == secret_number:
                log_to_file(f"Ollama guessed the correct number: {secret_number}")
                print("Ollama guessed the correct number!")
                break
            else:
                log_to_file(f"Ollama guessed wrong. The guess was {guess}, the correct number is {secret_number}")
                prompt = "No, keep trying with a different number, between 1 and 10. Respond only with the number."
        except ValueError:
            log_to_file(f"Ollama did not provide a valid number. Guess: {reply}")
            prompt = "No, keep trying with a different number, but only respond with the number."
        
        time.sleep(2)  # Optional: Add a small delay between retries

if __name__ == "__main__":
    main()

