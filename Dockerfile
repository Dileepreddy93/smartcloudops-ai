# Phase 2.3 Dockerfile - Simple Implementation (Per PDF Plan)
FROM python:3.10

# Copy app directory
COPY app/ /app

# Install dependencies
RUN pip install -r /app/requirements.txt

# Run Flask app
CMD ["python", "/app/main.py"]