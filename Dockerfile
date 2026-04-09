# Backend Dockerfile
FROM python:3.12-slim

WORKDIR /app

# Copy requirements and install
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy server files
COPY . .

# Expose the API port
EXPOSE 8000

# Run the backend
CMD ["python", "app.py"]
