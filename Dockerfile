FROM python:3.10-slim

# Set working directory
WORKDIR /app/hypexbt

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

# Copy requirements and install Python dependencies
COPY requirements.txt /app/
RUN pip install --no-cache-dir numpy==1.23.5
RUN pip install --no-cache-dir --no-deps -r /app/requirements.txt

# Copy the full app directory (including hypexbt/)
COPY . /app

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app/hypexbt

# Create non-root user
RUN useradd -m appuser
USER appuser

# Default command
CMD ["python", "-m", "bot.main", "--mode", "scheduler"]
