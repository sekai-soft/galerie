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

# Install project and uwsgi
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-dev && \
    apt-get update && apt-get -y install build-essential python3-dev && \
    uv pip install uwsgi==2.0.23

# Final stage - runtime image
FROM python:3.12-slim-bookworm

# Copy the application from builder
COPY --from=builder /app /app

# Set PATH to use the virtual environment
ENV PATH="/app/.venv/bin:$PATH"

WORKDIR /app

# Run uwsgi.ini when the container launches
CMD ["bash", "-c", "flask translate compile && flask digest compile && PORT=\"${PORT:=5000}\" && uwsgi --ini uwsgi.ini --http :${PORT}"]
