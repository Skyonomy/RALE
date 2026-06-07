# Use a slim Python image for efficiency
FROM python:3.12-slim

# Set environment variables for stability
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV FLASK_APP=app.py

# Install system dependencies (required for Pillow, etc.)
RUN apt-get update && apt-get install -y \
    libjpeg-dev \
    zlib1g-dev \
    libfreetype6-dev \
    liblcms2-dev \
    libopenjp2-7-dev \
    libtiff5-dev \
    tk-dev \
    tcl-dev \
    fonts-dejavu-core \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the entire project
COPY . .

# Expose the port
EXPOSE 5050

# Command to run the application
CMD ["gunicorn", "--bind", "0.0.0.0:5050", "--workers", "1", "--threads", "8", "--timeout", "300", "app:app"]
