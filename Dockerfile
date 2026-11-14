# API de Rastrojo (FastAPI). Imagen chica, sin secretos; los fixtures del lote demo van incluidos.
FROM python:3.12-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 UV_COMPILE_BYTECODE=1
RUN pip install --no-cache-dir uv==0.11.32
WORKDIR /app
COPY pyproject.toml uv.lock README.md ./
COPY src ./src
COPY data/assumptions.yaml data/glossary.yaml data/forbidden_phrases.yaml data/intents.yaml ./data/
COPY data/fixtures ./data/fixtures
RUN uv sync --frozen --no-dev
ENV DEMO_MODE=1 PORT=8000
EXPOSE 8000
CMD ["sh", "-c", "uv run --no-dev uvicorn rastrojo.adapters.api:app --host 0.0.0.0 --port ${PORT}"]
