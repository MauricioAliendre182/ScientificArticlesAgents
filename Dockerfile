# Multi-stage Dockerfile for Scientific Articles Engine

FROM python:3.11-slim as base

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Create app directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .

# Install Python dependencies
RUN pip install --upgrade pip && \
    pip install -r requirements.txt

# Copy application code
COPY src/ ./src/
COPY config.yaml .
COPY pyproject.toml .
COPY README.md .

# Install the package
RUN pip install -e .

# Create non-root user
RUN useradd -m -u 1000 appuser && \
    chown -R appuser:appuser /app

USER appuser

# Expose port (if adding web interface in future)
EXPOSE 8000

# Default command
CMD ["scientific-articles-engine", "--help"]

# Development stage
FROM base as development

USER root

# Install development dependencies
RUN pip install pytest pytest-asyncio pytest-cov pytest-mock \
    black ruff mypy

USER appuser

CMD ["/bin/bash"]

# Production stage
FROM base as production

# Health check (placeholder for future web interface)
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD ["python", "-c", "import scientific_articles_engine; print('OK')"]

ENTRYPOINT ["scientific-articles-engine"]
CMD ["--help"]
