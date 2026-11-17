# Use Python 3.11 slim image
FROM python:3.11-slim

# Update system and install dependencies
RUN apt-get update && apt-get install -y \
    default-jre \
    default-jdk \
    zipalign \
    curl \
    wget \
    && rm -rf /var/lib/apt/lists/*

# Copy Apktool JAR
COPY apktool.jar /usr/local/bin/apktool.jar
RUN echo '#!/bin/bash\njava -jar /usr/local/bin/apktool.jar "$@"' > /usr/local/bin/apktool && chmod +x /usr/local/bin/apktool

# Copy your Keystore
COPY my-release-key.jks /app/my-release-key.jks

# Working directory
WORKDIR /app

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy Bot Code
COPY main.py .

# Expose port (optional, but good practice)
EXPOSE 8080

# Command to run the bot
CMD ["python", "main.py"]
