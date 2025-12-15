# Use official Python 3.9 slim image
FROM python:3.9-slim

# Keep python output unbuffered and set locale
ENV PYTHONUNBUFFERED=1 \
    LANG=C.UTF-8 \
    CHROME_BIN=/usr/bin/chromium

WORKDIR /app

# Install system dependencies needed for audio, ffmpeg and a Chromium browser for Selenium
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    chromium \
    chromium-driver \
    build-essential \
    libsndfile1 \
    libasound2 \
    libasound2-dev \
    portaudio19-dev \
    libportaudio2 \
    wget \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Copy dependency manifest and install python deps
COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r /app/requirements.txt

# Copy application code
COPY . /app

# Optional: expose display variable for headless usage
ENV DISPLAY=:99

# Run the assistant
CMD ["python", "index.py"]

