# ---- Stage 1: Build environment ----
    FROM python:3.11 AS build

    # Set environment variables to reduce .pyc files and disable pip cache
    ENV PYTHONDONTWRITEBYTECODE=1 \
        PIP_NO_CACHE_DIR=1
    
    # Set working directory
    WORKDIR /app
    
    # Install dependencies early (cache layer)
    COPY requirements.txt  requirements.txt
    RUN pip install -r requirements.txt
    
    # Copy application source code
    COPY . .
    
    FROM python:3.11-slim
    
    # Install system-level dependencies required by packages like OpenCV, psycopg2, reportlab, etc.
    RUN apt-get update && apt-get install -y --no-install-recommends \
        libglib2.0-0 \
        libsm6 \
        libxext6 \
        libxrender-dev \
        libgl1-mesa-glx \
        libpq-dev \
        && apt-get clean && rm -rf /var/lib/apt/lists/*
    
    # Set work directory
    WORKDIR /app
    
    COPY --from=build /app /app
    
    # Expose FastAPI port
    EXPOSE 8000
    
    # Run FastAPI app with Uvicorn
    CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]
    