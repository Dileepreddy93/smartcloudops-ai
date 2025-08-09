# SmartCloudOps AI - Production-Ready Multi-Stage Docker Build
# Security-hardened with non-root user and health checks

# Build Stage
FROM python:3.10-slim as builder
WORKDIR /build
COPY app/requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

# Production Stage
FROM python:3.10-slim as production

# Security: Install security updates
RUN apt-get update && apt-get upgrade -y && \
    apt-get install -y --no-install-recommends curl && \
    rm -rf /var/lib/apt/lists/*

# Create non-root user for security
RUN groupadd -r appuser && useradd -r -g appuser appuser

# Set up application directory
WORKDIR /app
RUN chown appuser:appuser /app

# Install gunicorn in production stage
RUN pip install --no-cache-dir gunicorn==21.2.0

# Copy dependencies from builder stage
COPY --from=builder /root/.local /home/appuser/.local
ENV PATH=/home/appuser/.local/bin:$PATH

# Copy application code and scripts
COPY --chown=appuser:appuser app/ /app/
COPY --chown=appuser:appuser scripts/ /app/scripts/
COPY --chown=appuser:appuser data/ /app/data/
COPY --chown=appuser:appuser ml_models/ /app/ml_models/

# Add scripts directory to Python path for module imports
ENV PYTHONPATH=/app/scripts:/app:$PYTHONPATH
ENV ENVIRONMENT=production
ENV DEBUG=false

# Switch to non-root user
USER appuser

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:5000/status || exit 1

# Expose port
EXPOSE 5000

# 🔒 SECURITY: Use Gunicorn production server (NOT Flask dev server)
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "2", "--timeout", "120", "--worker-class", "sync", "--max-requests", "1000", "--max-requests-jitter", "100", "main:app"]