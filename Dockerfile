FROM python:3.11-slim

WORKDIR /app

# Install dependencies and curl for health check
RUN apt-get update && apt-get install -y --no-install-recommends curl \
    && rm -rf /var/lib/apt/lists/*
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application
COPY . .

# Expose the application port
EXPOSE 8000

# Health check to ensure the API is running
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
  CMD curl -f http://localhost:8000/health || exit 1

# Run the application
CMD gunicorn app:app --worker-class uvicorn.workers.UvicornWorker --bind 0.0.0.0:${PORT:-8000}
