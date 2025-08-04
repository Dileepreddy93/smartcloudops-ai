# Phase 2.3 Dockerfile - GPT Integration Ready (Per PDF Plan)
FROM python:3.10

# Copy app directory
COPY app/ /app

# Install dependencies
RUN pip install -r /app/requirements.txt

# Expose port
EXPOSE 5000

# Run Flask app
CMD ["python", "/app/main.py"]
CMD ["python", "/app/main.py"]