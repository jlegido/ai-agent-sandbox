FROM python:3.9-slim-buster

# Install necessary dependencies
RUN apt-get update && apt-get install -y \
    git \
    curl \
    docker.io \
    && rm -rf /var/lib/apt/lists/*

# Install Docker Compose V2 manually
RUN DOCKER_COMPOSE_VERSION=$(curl -s https://api.github.com/repos/docker/compose/releases/latest | grep tag_name | cut -d '"' -f 4) \
    && curl -L https://github.com/docker/compose/releases/download/${DOCKER_COMPOSE_VERSION}/docker-compose-linux-aarch64 -o /usr/local/bin/docker-compose \
    && chmod +x /usr/local/bin/docker-compose

# Set working directory
WORKDIR /app

# Copy the agent code
COPY agent.py .
COPY requirements.txt .

# Install Python dependencies
RUN pip install -r requirements.txt

# Entrypoint to run the agent
CMD ["python", "agent.py"]
