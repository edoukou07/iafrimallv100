# Stage 1: Builder - compile dependencies
FROM python:3.11-slim as builder

WORKDIR /build

RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    g++ \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Use consolidated requirements (includes PyTorch 2.0.1 + CLIP)
COPY requirements.txt requirements.txt
RUN pip install --user --no-cache-dir -r requirements.txt

# Stage 2: Runtime - minimal image
FROM python:3.11-slim

WORKDIR /app

# Copy only Python packages from builder
COPY --from=builder /root/.local /root/.local

# Install runtime dependencies (ffmpeg for Whisper audio processing)
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# Copy application
COPY app/ ./app/

# Create data directories
RUN mkdir -p /app/data /app/logs /app/uploads

ENV PATH=/root/.local/bin:$PATH
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONPATH=/app

# ACA uses PORT environment variable, default to 8000
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=10s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/api/v1/health').read()" || exit 1

# Run with gunicorn + uvicorn
CMD ["gunicorn", \
     "-w", "2", \
     "-k", "uvicorn.workers.UvicornWorker", \
     "--bind", "0.0.0.0:8000", \
     "--timeout", "60", \
     "--access-logfile", "-", \
     "--error-logfile", "-", \
     "--max-requests", "1000", \
     "app.main:app"]
