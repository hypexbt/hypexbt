FROM python:3.13-slim

# Set working directory to where your code will be
WORKDIR /app/hypexbt

# Install system dependencies for TA-Lib build
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc g++ wget make build-essential autoconf automake libtool \
    && rm -rf /var/lib/apt/lists/*

# Download and install TA-Lib native C library
RUN wget http://prdownloads.sourceforge.net/ta-lib/ta-lib-0.4.0-src.tar.gz && \
    tar -xvzf ta-lib-0.4.0-src.tar.gz && \
    cd ta-lib && ./configure --prefix=/usr && make && make install && \
    cd .. && rm -rf ta-lib ta-lib-0.4.0-src.tar.gz

# Copy project files into container
COPY . .

# Install dependencies using pip from pyproject.toml
RUN pip install --no-cache-dir -e .

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app/hypexbt

# Create a non-root user and switch
RUN useradd -m appuser
USER appuser

# Use WORKDIR where bot/ folder exists
WORKDIR /app/hypexbt

# Command to run your bot
RUN echo "Listing /app:"
RUN ls -l /app
RUN echo "Listing /app/hypexbt:"
RUN ls -l /app/hypexbt
RUN echo "Listing /app/hypexbt/bot:"
RUN ls -l /app/hypexbt/bot
CMD ["python", "-m", "bot.main", "--mode", "scheduler"]
