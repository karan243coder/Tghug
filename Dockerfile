# Optimized Dockerfile for Koyeb (512MB RAM)
FROM python:3.11-slim

WORKDIR /app

# ✅ FIXED: libgl1 use kiya instead of libgl1-mesa-glx
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    libglib2.0-0 \
    libgl1 \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

COPY requirements.txt .
RUN pip install --no-cache-dir --no-compile -r requirements.txt

COPY bot.py .

ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV MALLOC_TRIM_THRESHOLD_=100000
ENV PYTHONHASHSEED=42

HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import sys; print('OK'); sys.exit(0)"

CMD ["python", "-u", "bot.py"]
