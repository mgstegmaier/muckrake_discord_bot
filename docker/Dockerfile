# Multi-stage Dockerfile for Worldmind Discord Bot
# Stage 1: Builder - Install dependencies in isolated virtual environment
# Stage 2: Runtime - Minimal production image with PUID/PGID support

# ============================================================================
# Stage 1: Builder
# ============================================================================
FROM python:3.11-slim AS builder

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
FROM python:3.11-slim AS runtime

# Add metadata labels
LABEL maintainer="worldmind-bot"
LABEL description="Worldmind Discord Bot - Multi-server bot with role-based access control"
LABEL version="1.1"

# Install gosu for stepping down from root to specified user
RUN apt-get update && \
    apt-get install -y --no-install-recommends gosu && \
    rm -rf /var/lib/apt/lists/* && \
    gosu nobody true

# Copy virtual environment from builder stage
COPY --from=builder /opt/venv /opt/venv

# Set PATH to use virtual environment
ENV PATH="/opt/venv/bin:$PATH"

# Set working directory
WORKDIR /app

# Copy application files (excludes tests, docs, etc. per .dockerignore)
COPY app/ /app/app/

# Copy entrypoint script
COPY docker/entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

# Set Python to run in unbuffered mode for better logging
ENV PYTHONUNBUFFERED=1

# Default PUID/PGID (can be overridden at runtime)
ENV PUID=1000
ENV PGID=1000

# Set entrypoint
ENTRYPOINT ["/entrypoint.sh"]
