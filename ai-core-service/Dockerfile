FROM python:3.11-slim

WORKDIR /app

# Install uv
RUN pip install uv

# Copy project files
COPY ai-core-service/pyproject.toml ./
COPY ai-core-service/uv.lock ./
COPY ai-core-service/api ./api
COPY ai-core-service/ai ./ai
COPY ai-core-service/services ./services

# Copy shared services
COPY shared-services /shared-services

# Install dependencies
RUN uv sync --frozen

# Expose port
EXPOSE 8001

# Run service
CMD ["uv", "run", "uvicorn", "api.app:app", "--host", "0.0.0.0", "--port", "8001"]
