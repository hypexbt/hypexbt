FROM python:3.10-slim

WORKDIR /app

# Install build tools and TA-Lib native deps
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc g++ wget make build-essential autoconf automake libtool \
    && rm -rf /var/lib/apt/lists/*

# Build and install TA-Lib C library
RUN wget http://prdownloads.sourceforge.net/ta-lib/ta-lib-0.4.0-src.tar.gz && \
    tar -xvzf ta-lib-0.4.0-src.tar.gz && \
    cd ta-lib && \
    ./configure --prefix=/usr && \
    make && make install && \
    cd .. && rm -rf ta-lib ta-lib-0.4.0-src.tar.gz

# Copy requirements and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir numpy==1.23.5
RUN pip install --no-cache-dir --no-deps -r requirements.txt

# Copy entire project (including bot folder)
COPY . .

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app

# Create and switch to non-root user
RUN useradd -m appuser
USER appuser

# Run your main app module inside bot
CMD ["python", "-m", "bot.main", "--mode", "scheduler"]
