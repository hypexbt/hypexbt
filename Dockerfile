FROM python:3.10-slim

WORKDIR /app

# Install system dependencies for TA-Lib
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc g++ wget make build-essential autoconf automake libtool \
    && rm -rf /var/lib/apt/lists/*

# Install TA-Lib from source
RUN wget http://prdownloads.sourceforge.net/ta-lib/ta-lib-0.4.0-src.tar.gz && \
    tar -xvzf ta-lib-0.4.0-src.tar.gz && \
    cd ta-lib && \
    ./configure --prefix=/usr && \
    make && \
    make install && \
    cd .. && rm -rf ta-lib ta-lib-0.4.0-src.tar.gz

COPY . .

# Confirm files are present
RUN ls -l /app && cat requirements.txt

# Install numpy first (TA-Lib needs this order)
RUN pip install --no-cache-dir numpy==1.23.5

# Install remaining dependencies
RUN pip install --no-cache-dir --no-deps -r requirements.txt

# Run your app
CMD ["python", "-m", "bot.main", "--mode", "scheduler"]
