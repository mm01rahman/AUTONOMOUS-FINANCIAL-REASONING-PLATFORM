# syntax=docker/dockerfile:1.7
FROM python:3.11-slim AS builder

ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy

WORKDIR /workspace

COPY --from=ghcr.io/astral-sh/uv:0.12.0 /uv /usr/local/bin/uv
COPY pyproject.toml uv.lock README.md ./
COPY tools ./tools
COPY 00-governance ./00-governance
COPY 01-vision ./01-vision
COPY 02-architecture ./02-architecture
COPY 03-engineering ./03-engineering
COPY 04-ai-framework ./04-ai-framework
COPY 05-work-packages ./05-work-packages
COPY 06-runtime ./06-runtime
COPY 07-research ./07-research
COPY 09-validation ./09-validation
COPY REPOSITORY_MANIFEST.yaml ./

RUN uv sync --frozen --no-dev

FROM python:3.11-slim AS runtime

ENV PATH="/workspace/.venv/bin:${PATH}" \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

RUN groupadd --system --gid 10001 afrp \
    && useradd --system --uid 10001 --gid afrp --home-dir /nonexistent afrp

WORKDIR /workspace
COPY --from=builder --chown=afrp:afrp /workspace /workspace

USER 10001:10001

HEALTHCHECK --interval=30s --timeout=10s --retries=3 \
    CMD ["afrp", "boot"]

ENTRYPOINT ["afrp"]
CMD ["boot"]
