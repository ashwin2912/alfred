FROM python:3.11-slim

WORKDIR /app

# Install uv
RUN pip install uv

# Copy project files
COPY pyproject.toml ./
COPY bot ./bot
COPY scripts ./scripts

# Copy shared services
COPY --from=shared-services /shared-services /shared-services

# Install dependencies
RUN uv pip install --system -e .

# Run bot
CMD ["python", "-m", "bot.main"]
