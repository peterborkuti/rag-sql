# Build the Docker image
docker build -t rag-sql-app .

# Run the container
docker run -p 7860:7860 rag-sql-app

docker ps
docker exec -it <container_id> /bin/bash