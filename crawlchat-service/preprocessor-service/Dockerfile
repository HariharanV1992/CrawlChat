# PDF Preprocessing Service Dockerfile
FROM python:3.10-slim

# Install system dependencies for pdf2image and Poppler
RUN apt-get update && \
    apt-get install -y \
    poppler-utils \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy requirements first for better caching
COPY preprocessor-service/requirements-preprocessor.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements-preprocessor.txt

# Copy application code
COPY preprocessor-service/preprocessing_service.py .
COPY preprocessor-service/src/ ./src/

# Create non-root user for security
RUN useradd -m -u 1000 preprocessor && \
    chown -R preprocessor:preprocessor /app

USER preprocessor

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python3 -c "import preprocessing_service; print('OK')" || exit 1

CMD ["python3", "preprocessing_service.py"] 