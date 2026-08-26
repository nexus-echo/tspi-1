FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PYTHONPATH=/app \
    TSPI_MCP_TRANSPORT=streamable-http \
    TSPI_MCP_PORT=8080

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY tspi_mcp ./tspi_mcp

RUN useradd -m appuser && chown -R appuser /app
USER appuser

EXPOSE 8080
# Public surface: MUST run with TSPI_MCP_AUTH=jwt|workos (fail-closed if misconfigured).
CMD ["python", "-m", "tspi_mcp.server"]
