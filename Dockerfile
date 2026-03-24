# Backend Dockerfile for IndMoney Weekly Product Pulse

# 1. Base image
FROM python:3.11-slim-bookworm

# 2. Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app

# 3. Set work directory
WORKDIR /app

# 4. Install system dependencies for Playwright (Chromium)
RUN apt-get update && apt-get install -y --no-install-recommends \
    wget \
    gnupg \
    libnss3 \
    libnspr4 \
    libatk1.0-0 \
    libatk-bridge2.0-0 \
    libcups2 \
    libdrm2 \
    libxkbcommon0 \
    libxcomposite1 \
    libxdamage1 \
    libxext6 \
    libxfixes3 \
    libxrandr2 \
    libgbm1 \
    libasound2 \
    libpango-1.0-0 \
    libcairo2 \
    && rm -rf /var/lib/apt/lists/*

# 5. Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 6. Install Playwright browser
RUN playwright install chromium
RUN playwright install-deps chromium

# 7. Copy project files
COPY . .

# 8. Expose port (default FastAPI)
EXPOSE 8000

# 9. Run the application
CMD ["sh", "-c", "uvicorn module_e.api:app --host 0.0.0.0 --port ${PORT:-8000}"]
