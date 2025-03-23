FROM python:3.10-slim AS builder

WORKDIR /app

RUN apt-get update && apt-get install -y \
    curl \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Set cache directories to writable locations
ENV HF_HOME=/app/.cache
ENV TRANSFORMERS_CACHE=/app/.cache/huggingface/transformers
ENV SENTENCE_TRANSFORMERS_HOME=/app/.cache/torch/sentence_transformers

# Create cache directories with proper permissions
RUN mkdir -p /app/.cache/huggingface/transformers
RUN mkdir -p /app/.cache/torch/sentence_transformers
RUN chmod -R 777 /app/.cache

# Copy and install requirements
COPY requirements.txt .
RUN pip wheel --no-cache-dir --no-deps --wheel-dir /app/wheels -r requirements.txt

# Final stage
FROM python:3.10-slim

WORKDIR /app

# Install Ollama
RUN apt-get update && apt-get install -y curl && \
    curl -fsSL https://ollama.com/install.sh | sh && \
    rm -rf /var/lib/apt/lists/*

# Install netcat
RUN apt-get update && apt-get install -y netcat-traditional && \
    apt-get autoremove -y && \
    rm -rf /var/lib/apt/lists/*

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

# Copy wheels from builder stage
COPY --from=builder /app/wheels /wheels
RUN pip install --no-cache /wheels/*

RUN mkdir -p templates
RUN mkdir -p src
RUN mkdir -p data

# Copy application files
COPY src/ /app/src/
COPY templates/ /app/templates/
COPY data/ /app/data/
COPY __init__.py /app/

COPY docker_start.sh /app/start.sh
RUN chmod +x /app/start.sh

# Expose port
EXPOSE 7860
# Remove the CMD line which would conflict with ENTRYPOINT
ENTRYPOINT ["/app/start.sh"]
