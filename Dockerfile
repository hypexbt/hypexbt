FROM python:3.10-slim

WORKDIR /app

# Copy everything from your project directory into /app in the container
COPY . .

# List files and directories inside /app to check if 'bot' folder is there
RUN ls -l /app

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Run the app module inside bot
CMD ["python", "-m", "bot.main", "--mode", "scheduler"]
