# Use Python 3.11 to avoid the deprecation warning
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PORT=7860

# Install system dependencies (including those for Playwright/Crawl4AI if needed)
# We install basic build tools and libraries often needed by python packages
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    software-properties-common \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first to leverage Docker cache
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Install Playwright browsers (required by crawl4ai)
RUN playwright install --with-deps chromium

# Copy the rest of the application
COPY . .

# Expose the port (Hugging Face Spaces use 7860)
EXPOSE 7860

# Run the application
# We point to 'src' because we created src/agent.py
CMD ["adk", "web", "--host", "0.0.0.0", "--port", "7860", "src"]
