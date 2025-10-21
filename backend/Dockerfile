# Multi-stage build for Python backend
FROM python:3.11-slim as base

# Set working directory
WORKDIR /app

# Install system dependencies for build stage
FROM base as builder

RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    libffi-dev \
    libssl-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY backend/requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir --user -r requirements.txt

# Production stage
FROM base as production

# Create application user for security
RUN groupadd -r appuser && useradd -r -g appuser appuser

# Install only runtime dependencies
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Copy installed packages from builder stage
COPY --from=builder /root/.local /home/appuser/.local

# Copy application code from backend directory
COPY --chown=appuser:appuser backend/ .

# Copy frontend merchant files for integrated serving
COPY --chown=appuser:appuser frontend/merchant /app/frontend/merchant
COPY --chown=appuser:appuser frontend/css /app/frontend/css
COPY --chown=appuser:appuser frontend/js /app/frontend/js
COPY --chown=appuser:appuser frontend/admin /app/frontend/admin

# Create logs directory
RUN mkdir -p /app/logs /app/frontend && chown -R appuser:appuser /app

# Switch to non-root user
USER appuser

# Set environment variables
ENV PATH=/home/appuser/.local/bin:$PATH \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONHASHSEED=random

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Expose port
EXPOSE 8000

# Start command with production uvicorn settings
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4", "--access-log", "--log-level", "info"]