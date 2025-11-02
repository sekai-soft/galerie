# Builder stage - install dependencies with uv
FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim AS builder

ENV UV_COMPILE_BYTECODE=1 UV_LINK_MODE=copy

WORKDIR /app

# Install dependencies from lockfile (without the project itself)
RUN --mount=type=cache,target=/root/.cache/uv \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    --mount=type=bind,source=README.md,target=README.md \
    uv sync --frozen --no-install-project --no-dev

# Copy application code
ADD . /app

# Install project
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-dev

# Final stage - runtime image
FROM python:3.12-slim-bookworm

# Copy the application from builder
COPY --from=builder /app /app

# Set PATH to use the virtual environment
ENV PATH="/app/.venv/bin:$PATH"

# Install uwsgi with build dependencies, then clean up
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential python3-dev \
    && pip install uwsgi==2.0.23 \
    && apt-get remove -y build-essential python3-dev \
    && apt-get autoremove -y \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Run uwsgi.ini when the container launches
CMD ["bash", "-c", "flask translate compile && flask digest compile && PORT=\"${PORT:=5000}\" && uwsgi --ini uwsgi.ini --http :${PORT}"]
