# DistillAI - Multi-Platform Docker Deployment
#
# Usage:
#   docker build -t distillai .
#   docker run -p 5000:5000 -p 5001:5001 --env MINIMAX_API_KEY=your_key distillai
#
# Or docker-compose (see docker-compose.yml)

FROM python:3.11-slim

LABEL maintainer="DistillAI"
LABEL description="DistillAI v2.0 - AI Persona Platform"

# Install system deps (for any extended tools)
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Workdir
WORKDIR /app

# Copy application
COPY distill/ /app/distill/
COPY clients/ /app/clients/
COPY README.md /app/

# Install Python deps (Flask)
RUN pip install --no-cache-dir flask requests

# Environment variables
ENV PYTHONUNBUFFERED=1
ENV DISTILLAI_PORT=5000
ENV DISTILLAI_WEBHOOK_PORT=5001

# Expose ports
EXPOSE 5000 5001

# Health check
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:5000/health || exit 1

# Run
CMD ["python", "distill/api/server.py"]