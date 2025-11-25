
# Use the official UV Python base image with Python 3.13 on Debian Bookworm
# UV is a fast Python package manager that provides better performance than pip
# We use the slim variant to keep the image size smaller while still having essential tools
ARG PYTHON_VERSION=3.13
FROM ghcr.io/astral-sh/uv:python${PYTHON_VERSION}-bookworm-slim AS base

# Keeps Python from buffering stdout and stderr to avoid situations where
# the application crashes without emitting any logs due to buffering.
ENV PYTHONUNBUFFERED=1

# Create a non-privileged user that the app will run under.
# See https://docs.docker.com/develop/develop-images/dockerfile_best-practices/#user
ARG UID=10001
RUN adduser \
    --disabled-password \
    --gecos "" \
    --home "/app" \
    --shell "/sbin/nologin" \
    --uid "${UID}" \
    appuser

# Install build dependencies + Node.js
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    python3-dev \
    curl \
  && rm -rf /var/lib/apt/lists/*

# Install Node.js and pnpm
#RUN curl -fsSL https://deb.nodesource.com/setup_20.x | bash - \
#  && apt-get install -y nodejs \
#  && npm install -g pnpm


  WORKDIR /app

# Copy everything first
COPY . .

# Build frontend
#WORKDIR /app/web
#RUN pnpm install
#RUN pnpm build

# Back to app root for Python setup
WORKDIR /app

# Install Python dependencies
RUN uv sync --locked

RUN chown -R appuser:appuser /app
USER appuser

RUN uv run src/agent.py download-files

CMD ["uv", "run", "src/agent.py", "start"]