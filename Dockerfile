FROM python:3.10-slim

WORKDIR /app

# Install system dependencies (for TA-Lib)
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc g++ wget make build-essential autoconf automake libtool && \
    rm -rf /var/lib/apt/lists/*

# Build and install TA-Lib C library
RUN wget http://prdownloads.sourceforge.net/ta-lib/ta-lib-0.4.0-src.tar.gz && \
    tar -xvzf ta-lib-0.4.0-src.tar.gz && \
    cd ta-lib && ./configure --prefix=/usr && make && make install && \
    cd .. && rm -rf ta-lib ta-lib-0.4.0-src.tar.gz

# Copy project files
COPY . .

# Install numpy first
RUN pip install --no-cache-dir numpy==1.23.5

# Then install other Python dependencies (without numpy)
RUN pip install --no-cache-dir --no-deps -r requirements.txt

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app

# Create non-root user
RUN useradd -m appuser
USER appuser

# Run your main bot module
CMD ["python", "-m", "bot.main", "--mode", "scheduler"]
