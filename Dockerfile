FROM python:3.13-slim

# set work directory
WORKDIR /app

# Install Node.js for Vite build
RUN apt-get update && apt-get install -y curl gnupg git && \
    curl -fsSL https://deb.nodesource.com/setup_20.x | bash - && \
    apt-get install -y nodejs && \
    rm -rf /var/lib/apt/lists/*

# install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# copy project
COPY . .

# Synchronize dependencies (install all production dependencies)
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-dev

# Set environment to use the virtual environment
ENV VIRTUAL_ENV=/app/.venv \
    PATH="/app/.venv/bin:$PATH"

# Verify critical dependencies are installed
RUN python -c "import psycopg2; print(f'✅ psycopg2 {psycopg2.__version__} installed')" && \
    python -c "import django; print(f'✅ Django {django.__version__} installed')" && \
    python -c "import uvicorn; print(f'✅ uvicorn installed')"

# Build Vite assets
WORKDIR /app/vite/src
RUN npm ci && npm run build

# Return to app directory
WORKDIR /app
RUN mkdir -p logs

# Run uvicorn directly from virtual environment
CMD ["gunicorn", "ta3lem.wsgi:application", "--bind", "0.0.0.0:8000"]