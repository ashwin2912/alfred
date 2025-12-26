FROM python:3.11-slim

WORKDIR /app

# Install uv
RUN pip install uv

# Copy project files
COPY pyproject.toml ./
COPY api ./api
COPY ai ./ai
COPY services ./services

# Copy shared services
COPY --from=shared-services /shared-services /shared-services

# Install dependencies
RUN uv pip install --system -e .

# Expose port
EXPOSE 8001

# Run service
CMD ["uvicorn", "api.app:app", "--host", "0.0.0.0", "--port", "8001"]
