FROM python:3.12-slim

WORKDIR /app

# Install dependencies in a single layer
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        curl \
        redis-tools && \
    rm -rf /var/lib/apt/lists/*

# Copy and install requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

# Copy entrypoint script and make it executable
COPY entrypoint.sh .
RUN chmod +x entrypoint.sh

# Copy application code
COPY . .

ENTRYPOINT ["./entrypoint.sh"]