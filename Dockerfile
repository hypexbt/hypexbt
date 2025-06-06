FROM python:3.10-slim

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

# Copy requirements file first for caching
COPY requirements.txt .

# Install numpy first (compatible version)
RUN pip install --no-cache-dir numpy==1.23.5

# Install rest of dependencies without reinstalling numpy
RUN pip install --no-cache-dir --no-deps -r requirements.txt

# Explicitly copy the bot directory and any other source code
COPY bot ./bot

# Copy any other files you need (adjust if you have more folders or files)
COPY . .

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app

# Create a non-root user and switch to it
RUN useradd -m appuser
USER appuser

# Run the main entry point with the correct module path
CMD ["python", "-m", "bot.main", "--mode", "scheduler"]
