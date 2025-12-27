FROM python:3.11-slim

WORKDIR /app

# Install uv
RUN pip install uv

# Copy project files
COPY discord-bot/pyproject.toml ./
COPY discord-bot/uv.lock ./
COPY discord-bot/bot ./bot
COPY discord-bot/scripts ./scripts

# Copy shared services
COPY shared-services /shared-services

# Install dependencies
RUN uv sync --frozen

# Run bot
CMD ["uv", "run", "python", "-m", "bot.bot"]
