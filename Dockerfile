# SmartCloudOps AI - Production-Ready Multi-Stage Docker Build
# Security-hardened with non-root user and health checks

# Build Stage
FROM python:3.10-slim as builder
WORKDIR /build
COPY app/requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

# Production Stage
FROM python:3.10-slim as production

# Create non-root user for security
RUN groupadd -r appuser && useradd -r -g appuser appuser

# Set up application directory
WORKDIR /app
RUN chown appuser:appuser /app

# Copy dependencies from builder stage
COPY --from=builder /root/.local /home/appuser/.local
ENV PATH=/home/appuser/.local/bin:$PATH

# Copy application code and scripts
COPY --chown=appuser:appuser app/ /app/
COPY --chown=appuser:appuser scripts/ /app/scripts/
COPY --chown=appuser:appuser data/ /app/data/
COPY --chown=appuser:appuser ml_models/ /app/ml_models/

# Switch to non-root user
USER appuser

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:5000/status', timeout=5)" || exit 1

# Expose port
EXPOSE 5000

# Production server command
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "2", "--timeout", "120", "main:app"]