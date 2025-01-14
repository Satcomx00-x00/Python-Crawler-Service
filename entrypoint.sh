#!/bin/bash
set -e

# Validate Redis connection parameters
if [[ -z "${REDIS_PORT}" ]] || ! [[ "${REDIS_PORT}" =~ ^[0-9]+$ ]]; then
    echo "Invalid REDIS_PORT. Setting default: 6379"
    export REDIS_PORT=6379
fi

if [[ -z "${REDIS_DB}" ]] || ! [[ "${REDIS_DB}" =~ ^[0-9]+$ ]]; then
    echo "Invalid REDIS_DB. Setting default: 0"
    export REDIS_DB=0
fi

# Wait for Redis
max_retries=5
count=0
echo "Waiting for Redis..."

until redis-cli -h ${REDIS_HOST} -p ${REDIS_PORT} ping 2>/dev/null || [ $count -eq $max_retries ]; do
    count=$((count+1))
    echo "Attempt $count/$max_retries: Redis is unavailable - sleeping 5s"
    sleep 5
done

if [ $count -eq $max_retries ]; then
    echo "Redis connection failed after $max_retries attempts"
    exit 1
fi

echo "Redis is available"

# Start the application
exec python website.py