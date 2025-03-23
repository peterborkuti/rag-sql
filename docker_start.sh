#!/bin/bash

# Start Ollama in the background
ollama serve &
OLLAMA_PID=$!

ls -lR

# Set up Python path to include app root
export PYTHONPATH=/app:/app/src:$PYTHONPATH

# Start the Flask app with waitress
echo "Starting web application on port 7860..."
cd /app && python -c "from src import flask_retriever; from waitress import serve; serve(flask_retriever.app, host='0.0.0.0', port=7860)"

# If the Flask app exits, also stop Ollama
kill $OLLAMA_PID