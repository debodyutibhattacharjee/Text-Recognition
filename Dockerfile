# Use a lightweight Python image
FROM python:3.10-slim

# Install system-level dependencies including tesseract-ocr
RUN apt-get update && apt-get install -y \
    tesseract-ocr \
    libsm6 \
    libxext6 \
    libglib2.0-0 \
    libgl1 \
    && apt-get clean

# Set the working directory inside the container
WORKDIR /app

# Copy all project files to the container
COPY . .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Expose the port used by Flask
EXPOSE 5000

# Command to run the server
CMD ["python", "server.py"]
