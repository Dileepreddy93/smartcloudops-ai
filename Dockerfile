# Phase 2.3 Dockerfile - Exact PDF Plan Implementation
FROM python:3.10
COPY app/ /app
RUN pip install -r /app/requirements.txt
CMD ["python", "/app/main.py"]
CMD ["python", "/app/main.py"]