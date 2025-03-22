FROM python:3.9-slim-buster

# Install necessary dependencies
RUN apt-get update && apt-get install -y \
    git \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Docker manually
RUN curl -fsSL https://get.docker.com -o get-docker.sh \
    && sh get-docker.sh

# Set working directory
WORKDIR /app

# Copy the agent code
COPY agent.py .
COPY requirements.txt .

# Install Python dependencies
RUN pip install -r requirements.txt

# Define environment variables
ENV MODEL="deepseek-coder"

# Entrypoint to run the agent
CMD ["python", "agent.py"]
