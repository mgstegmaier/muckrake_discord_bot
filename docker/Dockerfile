# Multi-stage Dockerfile for Worldmind Discord Bot
# Stage 1: Builder - Install dependencies in isolated virtual environment
# Stage 2: Runtime - Minimal production image with non-root user

# ============================================================================
# Stage 1: Builder
# ============================================================================
FROM python:3.11-slim as builder

# Install build dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        gcc \
        && rm -rf /var/lib/apt/lists/*

# Create virtual environment
RUN python -m venv /opt/venv

# Activate virtual environment
ENV PATH="/opt/venv/bin:$PATH"

# Copy requirements file
COPY requirements.txt .

# Install Python dependencies into virtual environment
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# ============================================================================
# Stage 2: Runtime
# ============================================================================
FROM python:3.11-slim as runtime

# Add metadata labels
LABEL maintainer="worldmind-bot"
LABEL description="Worldmind Discord Bot - Multi-server bot with role-based access control"
LABEL version="1.0"

# Create non-root user (UID 1000)
RUN useradd --create-home --uid 1000 --shell /bin/bash botuser

# Copy virtual environment from builder stage
COPY --from=builder /opt/venv /opt/venv

# Set PATH to use virtual environment
ENV PATH="/opt/venv/bin:$PATH"

# Set working directory
WORKDIR /app

# Copy application files (excludes tests, docs, etc. per .dockerignore)
COPY app/ /app/app/

# Change ownership to non-root user
RUN chown -R botuser:botuser /app

# Switch to non-root user
USER botuser

# Set Python to run in unbuffered mode for better logging
ENV PYTHONUNBUFFERED=1

# Expose health check port (configurable via env var)
EXPOSE 8080

# Set entrypoint to run the bot
ENTRYPOINT ["python", "-m", "app.bot"]
