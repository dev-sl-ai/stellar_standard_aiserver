# Use an official lightweight Python image
FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV DEBIAN_FRONTEND=noninteractive
# Persist logs outside the container's writable layer; bind-mount this at runtime
# (e.g. -v /opt/aiserver/logs:/app/logs) so logs survive container removal.
ENV LOG_DIR=/app/logs

# Install system dependencies for FAISS, OpenCV, etc.
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    cmake \
    libgl1 \
    libglib2.0-0 \
    wget \
    curl \
    unzip \
    && rm -rf /var/lib/apt/lists/*

# Create and set working directory
WORKDIR /app

# Copy dependency list to leverage Docker cache
COPY requirements.txt .

# Install Python dependencies
RUN pip install --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy only what the app needs at runtime (avoids pulling in .git, *.tar, etc.)
COPY runner.py shutdown.py ./
COPY .env ./
COPY src/ ./src/
COPY data/ ./data/

# Persisted log directory (bind-mount to a host folder at runtime)
VOLUME ["/app/logs"]

# Expose FastAPI port
EXPOSE 8080

# Start your runner
CMD ["python", "runner.py"]

