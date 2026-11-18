FROM python:3.11-slim

# Install Java
RUN apt-get update && apt-get install -y \
    default-jre-headless \
    curl \
    wget \
    && rm -rf /var/lib/apt/lists/*

# Create APKTool directory
RUN mkdir -p /opt/apktool

# Copy APKTool JAR
COPY apktool/apktool_3.0.3.jar /opt/apktool/apktool.jar

# Create APKTool launcher
RUN printf '#!/bin/sh\nexec java -jar /opt/apktool/apktool.jar "$@"\n' \
    > /usr/local/bin/apktool && \
    chmod +x /usr/local/bin/apktool

# Working directory
WORKDIR /app

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy Python application
COPY main.py .

# Start application
CMD ["python", "main.py"]
