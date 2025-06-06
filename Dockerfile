FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies + build tools for TA-Lib
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    g++ \
    wget \
    make \
    build-essential \
    autoconf \
    automake \
    libtool \
    && rm -rf /var/lib/apt/lists/*

# Download, build, and install TA-Lib native C library
RUN wget http://prdownloads.sourceforge.net/ta-lib/ta-lib-0.4.0-src.tar.gz && \
    tar -xvzf ta-lib-0.4.0-src.tar.gz && \
    cd ta-lib && \
    ./configure --prefix=/usr && \
    make && \
    make install && \
    cd .. && rm -rf ta-lib ta-lib-0.4.0-src.tar.gz

# Copy requirements file
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app

# Create non-root user
RUN useradd -m appuser
USER appuser

# Command to run the scheduler
CMD ["python", "-m", "bot.main", "--mode", "scheduler"]
