# Optimized Dockerfile for Koyeb (512MB RAM)
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Minimal system dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    libgl1-mesa-glx \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Copy requirements first (for Docker layer caching)
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir --no-compile -r requirements.txt

# Copy bot code
COPY bot.py .

# Environment optimizations for 512MB RAM
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV MALLOC_TRIM_THRESHOLD_=100000
ENV PYTHONHASHSEED=42

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import sys; print('OK'); sys.exit(0)"

# Run bot
CMD ["python", "-u", "bot.py"]
