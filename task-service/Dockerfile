FROM python:3.11-slim

WORKDIR /app

# Install uv
RUN pip install uv

# Copy project files
COPY task-service/pyproject.toml ./
COPY task-service/uv.lock ./
COPY task-service/api ./api
COPY task-service/services ./services

# Copy shared services
COPY shared-services /shared-services

# Install dependencies
RUN uv sync --frozen

# Expose port
EXPOSE 8002

# Run service
CMD ["uv", "run", "uvicorn", "api.app:app", "--host", "0.0.0.0", "--port", "8002"]
