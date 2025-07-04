# 🚀 GhuntRED-v2 Backend - Python 3.12 + Django 5.0
# Multi-stage build for optimal performance and security

# =============================================================================
# STAGE 1: Build Dependencies
# =============================================================================
FROM python:3.12-slim as builder

# Build arguments
ARG BUILD_ENV=production
ARG POETRY_VERSION=1.7.1

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    POETRY_NO_INTERACTION=1 \
    POETRY_VENV_IN_PROJECT=1 \
    POETRY_CACHE_DIR=/tmp/poetry_cache

# Install system dependencies for building
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    git \
    libpq-dev \
    libffi-dev \
    libssl-dev \
    pkg-config \
    && rm -rf /var/lib/apt/lists/*

# Install Poetry
RUN pip install poetry==$POETRY_VERSION

# Copy dependency files
WORKDIR /app
COPY pyproject.toml poetry.lock* ./

# Configure poetry and install dependencies
RUN poetry install --no-dev --no-root && rm -rf $POETRY_CACHE_DIR

# =============================================================================
# STAGE 2: Development Image
# =============================================================================
FROM python:3.12-slim as development

# Install runtime dependencies
RUN apt-get update && apt-get install -y \
    curl \
    libpq5 \
    libffi8 \
    libssl3 \
    netcat-openbsd \
    procps \
    && rm -rf /var/lib/apt/lists/*

# Create app user for security
RUN groupadd -r app && useradd -r -g app app

# Set work directory
WORKDIR /app

# Copy virtual environment from builder
COPY --from=builder --chown=app:app /app/.venv /app/.venv

# Ensure PATH includes virtual environment
ENV PATH="/app/.venv/bin:$PATH"

# Copy application code
COPY --chown=app:app . .

# Create necessary directories
RUN mkdir -p /app/logs /app/media /app/static && \
    chown -R app:app /app

# Install additional development tools
RUN pip install --no-cache-dir \
    ipython \
    jupyter \
    django-debug-toolbar \
    django-silk \
    pytest-django \
    pytest-cov

# Switch to non-root user
USER app

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health/ || exit 1

# Default command for development
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]

# =============================================================================
# STAGE 3: Production Image
# =============================================================================
FROM python:3.12-slim as production

# Install runtime dependencies
RUN apt-get update && apt-get install -y \
    curl \
    libpq5 \
    libffi8 \
    libssl3 \
    netcat-openbsd \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Create app user for security
RUN groupadd -r app && useradd -r -g app app

# Set work directory
WORKDIR /app

# Copy virtual environment from builder
COPY --from=builder --chown=app:app /app/.venv /app/.venv

# Ensure PATH includes virtual environment
ENV PATH="/app/.venv/bin:$PATH"

# Copy application code
COPY --chown=app:app . .

# Create necessary directories
RUN mkdir -p /app/logs /app/media /app/static && \
    chown -R app:app /app

# Set environment for production
ENV DJANGO_SETTINGS_MODULE=backend.config.settings.production \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

# Collect static files
RUN python manage.py collectstatic --noinput

# Switch to non-root user
USER app

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health/ || exit 1

# Default command for production
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "--workers", "4", "--worker-class", "gevent", "--worker-connections", "1000", "--max-requests", "1000", "--max-requests-jitter", "50", "--timeout", "120", "--keep-alive", "5", "backend.config.wsgi:application"]

# =============================================================================
# STAGE 4: ML-Optimized Image (for ML workloads)
# =============================================================================
FROM python:3.12-slim as ml-worker

# Install ML-specific dependencies
RUN apt-get update && apt-get install -y \
    curl \
    libpq5 \
    libffi8 \
    libssl3 \
    libgomp1 \
    libopenblas-dev \
    netcat-openbsd \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Create app user for security
RUN groupadd -r app && useradd -r -g app app

# Set work directory
WORKDIR /app

# Copy virtual environment from builder
COPY --from=builder --chown=app:app /app/.venv /app/.venv

# Ensure PATH includes virtual environment
ENV PATH="/app/.venv/bin:$PATH"

# Install additional ML packages
RUN pip install --no-cache-dir \
    tensorflow==2.15.0 \
    torch==2.1.2 \
    transformers==4.36.2 \
    scikit-learn==1.3.2 \
    numpy==1.24.4 \
    pandas==2.1.4 \
    joblib==1.3.2

# Copy application code
COPY --chown=app:app . .

# Create necessary directories
RUN mkdir -p /app/logs /app/media /app/static /app/ml/models && \
    chown -R app:app /app

# Set ML-specific environment variables
ENV OMP_NUM_THREADS=4 \
    OPENBLAS_NUM_THREADS=4 \
    MKL_NUM_THREADS=4 \
    VECLIB_MAXIMUM_THREADS=4 \
    NUMEXPR_NUM_THREADS=4 \
    TF_CPP_MIN_LOG_LEVEL=2

# Switch to non-root user
USER app

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health/ || exit 1

# Default command for ML workers
CMD ["celery", "-A", "backend.config.celery", "worker", "-l", "info", "-Q", "ml,genia,aura", "--concurrency=2", "--prefetch-multiplier=1"]