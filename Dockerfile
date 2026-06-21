FROM python:3.10-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    ffmpeg \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install yt-dlp via pip to ensure it is always the latest version
RUN pip install --no-cache-dir yt-dlp

# Set working directory
WORKDIR /app

# Copy server code
COPY server.py .

# Expose port
EXPOSE 8889

# Run the server
CMD ["python", "server.py"]
