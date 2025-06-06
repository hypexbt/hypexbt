FROM python:3.10-slim

WORKDIR /app

# Install system dependencies for ta-lib
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc g++ wget make build-essential autoconf automake libtool && \
    rm -rf /var/lib/apt/lists/*

# Build and install TA-Lib C lib
RUN wget http://prdownloads.sourceforge.net/ta-lib/ta-lib-0.4.0-src.tar.gz && \
    tar -xvzf ta-lib-0.4.0-src.tar.gz && \
    cd ta-lib && ./configure --prefix=/usr && make && make install && cd .. && \
    rm -rf ta-lib ta-lib-0.4.0-src.tar.gz

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY . .

ENV PYTHONPATH=/app

CMD ["python", "-m", "bot.main", "--mode", "scheduler"]
