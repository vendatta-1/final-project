# Official Python 3.11 base image
FROM python:3.11-slim

# Create a non-root user (required by Hugging Face Spaces)
RUN useradd -m -u 1000 user
USER user
ENV PATH="/home/user/.local/bin:$PATH"

WORKDIR /app

COPY --chown=user ./requirements.txt requirements.txt
USER root

# Install system dependencies for OpenCV, ReportLab, psycopg2, etc. debian distribution requirements 
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

USER user

RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

COPY --chown=user . /app

EXPOSE 7860

CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "7860"]
