# read the doc: https://huggingface.co/docs/hub/spaces-sdks-docker
# you will also find guides on how best to write your Dockerfile

FROM python:3.9

# The two following lines are requirements for the Dev Mode to be functional
# Learn more about the Dev Mode at https://huggingface.co/dev-mode-explorers
RUN useradd -m -u 1000 user
WORKDIR /app

COPY --chown=user ./requirements.txt requirements.txt
RUN pip install --no-cache-dir --upgrade -r requirements.txt

# Install Ollama
RUN apt-get update && apt-get install -y curl && \
    curl -fsSL https://ollama.com/install.sh | sh

# Install netcat
RUN apt-get update && apt-get install -y netcat-traditional && \
    apt-get autoremove -y

    # Switch to the "user" user

# Add this after installing Ollama but before using it:
RUN mkdir -p $HOME/.ollama && chmod 777 $HOME/.ollama

USER user

RUN ollama serve & \
    PID=$! && \
    for i in $(seq 1 30); do \
      if nc -z localhost 11434; then \
        break; \
      fi; \
      echo "Waiting for Ollama to start..."; \
      sleep 1; \
    done && \
    ollama pull llama3 && \
    kill $PID && \
    wait $PID

COPY --chown=user . /app

ENV HOME=/home/user \
  PATH=/home/user/.local/bin:$PATH

RUN chmod +x /app/docker_start.sh

# Expose port
EXPOSE 7860
# Remove the CMD line which would conflict with ENTRYPOINT
ENTRYPOINT ["/app/docker_start.sh"]
