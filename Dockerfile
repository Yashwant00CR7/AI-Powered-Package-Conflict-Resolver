# Use Python 3.11 to avoid the deprecation warning
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app \
    PORT=7860

# Install system dependencies (including those for Playwright/Crawl4AI if needed)
# We install basic build tools and libraries often needed by python packages
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first to leverage Docker cache
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Install Playwright browsers (required by crawl4ai)
RUN playwright install --with-deps chromium

# Copy the rest of the application
COPY . .

# Expose the port for Hugging Face Spaces
EXPOSE 7860

# Run the combined server
CMD ["python", "src/combined_server.py"]
