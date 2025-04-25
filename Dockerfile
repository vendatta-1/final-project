# Official Python 3.11 base image
FROM python:3.11-slim

# Create a non-root user (required by Hugging Face Spaces)
RUN useradd -m -u 1000 user
USER user
ENV PATH="/home/user/.local/bin:$PATH"

# Set working directory
WORKDIR /app

# Copy requirements file and switch to root for apt installs
COPY --chown=user ./requirements.txt requirements.txt
USER root

# Install system dependencies for OpenCV, ReportLab, psycopg2, etc.
RUN apt-get update && apt-get install -y \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    libgl1-mesa-glx \
    libpq-dev \
    gcc \
    g++ \
    libffi-dev \
    libjpeg-dev \
    libfreetype6-dev \
    libssl-dev \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

# Switch back to non-root user for Python installs
USER user

# Install Python packages
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

# Copy project files
COPY --chown=user . /app

# Expose port required by Hugging Face Spaces
EXPOSE 7860

# Command to run the FastAPI app
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "7860"]
