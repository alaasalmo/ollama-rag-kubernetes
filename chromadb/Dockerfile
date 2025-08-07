# Use an official Python base image
FROM python:3.12-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Set work directory
WORKDIR /app

# Install ChromaDB from PyPI
RUN pip install --upgrade pip
RUN pip install chromadb

# Expose Chroma HTTP server port
EXPOSE 8000

# Start the Chroma HTTP API server when the container runs
ENTRYPOINT ["chroma", "run", "--host", "0.0.0.0", "--port", "8000"]
#ENTRYPOINT ["tail"]
#CMD ["-f","/dev/null"]
