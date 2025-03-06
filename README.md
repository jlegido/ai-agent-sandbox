# ai-agent-sandbox
AI agent Sandbox

# Requirements

-Docker installed
-Depending the model that you want to install in ollama a cert amount of RAM memory and disk space. See https://github.com/ollama/ollama?tab=readme-ov-file#model-library

# Installation

1. Bring up docker containers

```
docker compose up --build -d
```

2. Once `ollama` container is started, install a model, for instance:

```
docker exec -it ollama ollama run llama3.2:1b
```

3. Open a browser and access WebUI

```
http://localhost:3000
```

4. Only one time, introduce:

-Username
-E-mail
-Password

Those credentials will be required if later on you want to login again

# Usage

Bring up docker containers:

```
docker compose up --build -d
```

## API

1. Get private IP of `ollama` docker container

```
docker inspect -f '{{range.NetworkSettings.Networks}}{{.IPAddress}}{{end}}' ollama
```

API is exposed in TCP port 11434 of that IP

## Web chat

http://localhost:3000


# Agent

A docker container called `agent` will ask ollama and write back reply in local file
