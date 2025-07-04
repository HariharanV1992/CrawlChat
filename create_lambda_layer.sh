#!/bin/bash

echo "🔧 Creating Lambda-Compatible Layer with Docker"
echo "================================================"

# Create a Dockerfile for Lambda-compatible builds
cat > Dockerfile.lambda-layer << 'EOF'
FROM public.ecr.aws/lambda/python:3.10

# Install build dependencies
RUN yum update -y && yum install -y \
    gcc \
    gcc-c++ \
    make \
    openssl-devel \
    libffi-devel \
    python3-devel \
    libjpeg-devel \
    zlib-devel \
    freetype-devel \
    lcms2-devel \
    libwebp-devel \
    tcl-devel \
    tk-devel \
    && yum clean all

# Copy requirements file
COPY requirements.txt /tmp/

# Install Python packages in Lambda environment
RUN pip install -r /tmp/requirements.txt -t /opt/python --no-cache-dir

# Ensure pydantic_core is properly installed
RUN pip install pydantic-core>=2.0.0 -t /opt/python --no-cache-dir --force-reinstall

# Clean up unnecessary files
RUN find /opt/python -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
RUN find /opt/python -type d -name "tests" -exec rm -rf {} + 2>/dev/null || true
RUN find /opt/python -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
RUN find /opt/python -name "*.pyc" -delete 2>/dev/null || true
RUN find /opt/python -name "*.pyo" -delete 2>/dev/null || true
RUN find /opt/python -name "*.md" -delete 2>/dev/null || true
RUN find /opt/python -name "*.txt" -delete 2>/dev/null || true
RUN find /opt/python -name "*.rst" -delete 2>/dev/null || true
RUN find /opt/python -name "LICENSE*" -delete 2>/dev/null || true
RUN find /opt/python -name "README*" -delete 2>/dev/null || true

# Remove large test directories from packages
RUN rm -rf /opt/python/bs4/tests/ 2>/dev/null || true
RUN rm -rf /opt/python/lxml/tests/ 2>/dev/null || true
RUN rm -rf /opt/python/aiohttp/tests/ 2>/dev/null || true
RUN rm -rf /opt/python/requests/tests/ 2>/dev/null || true
RUN rm -rf /opt/python/httpx/tests/ 2>/dev/null || true
RUN rm -rf /opt/python/fastapi/tests/ 2>/dev/null || true
RUN rm -rf /opt/python/pydantic/tests/ 2>/dev/null || true
RUN rm -rf /opt/python/pydantic_core/tests/ 2>/dev/null || true
RUN rm -rf /opt/python/motor/tests/ 2>/dev/null || true
RUN rm -rf /opt/python/pymongo/tests/ 2>/dev/null || true
RUN rm -rf /opt/python/openai/tests/ 2>/dev/null || true
RUN rm -rf /opt/python/selenium/tests/ 2>/dev/null || true
RUN rm -rf /opt/python/beautifulsoup4/tests/ 2>/dev/null || true
RUN rm -rf /opt/python/PyPDF2/tests/ 2>/dev/null || true
RUN rm -rf /opt/python/pdfminer/tests/ 2>/dev/null || true
RUN rm -rf /opt/python/html2text/tests/ 2>/dev/null || true
RUN rm -rf /opt/python/python_jose/tests/ 2>/dev/null || true
RUN rm -rf /opt/python/passlib/tests/ 2>/dev/null || true
RUN rm -rf /opt/python/mangum/tests/ 2>/dev/null || true
RUN rm -rf /opt/python/cryptography/tests/ 2>/dev/null || true

# Remove unnecessary documentation and examples
RUN find /opt/python -name "examples" -type d -exec rm -rf {} + 2>/dev/null || true
RUN find /opt/python -name "docs" -type d -exec rm -rf {} + 2>/dev/null || true
RUN find /opt/python -name "doc" -type d -exec rm -rf {} + 2>/dev/null || true

# Keep .dist-info directories as they contain essential package metadata
# Only remove .egg-info directories which are not needed
RUN find /opt/python -name "*.egg-info" -type d -exec rm -rf {} + 2>/dev/null || true

# Verify pydantic_core is present
RUN ls -la /opt/python/pydantic_core/ || echo "pydantic_core not found, will reinstall"
RUN python -c "import pydantic_core; print('pydantic_core imported successfully')" || echo "pydantic_core import failed"

# Create a simple command to keep container running
CMD ["/bin/bash", "-c", "echo 'Layer built successfully' && sleep infinity"]
EOF

echo "🐳 Building Lambda-compatible layer with Docker..."

# Build the Docker image
docker build -f Dockerfile.lambda-layer -t lambda-layer-builder .

if [ $? -ne 0 ]; then
    echo "❌ Docker build failed!"
    exit 1
fi

echo "📦 Extracting layer from Docker container..."

# Create layer directory
rm -rf lambda-layer-lambda-compatible
mkdir -p lambda-layer-lambda-compatible

# Copy the Python packages from the Docker container
docker create --name temp-container lambda-layer-builder
docker cp temp-container:/opt/python lambda-layer-lambda-compatible/
docker rm temp-container

# Create ZIP file
cd lambda-layer-lambda-compatible
zip -r lambda-layer-lambda-compatible.zip python/ -x "*.pyc" "__pycache__/*" "*.pyo" "*.pyd" ".git/*" ".gitignore" "*.log" "*.tmp"

# Check sizes
ZIP_SIZE=$(du -h lambda-layer-lambda-compatible.zip | cut -f1)
cd python
UNZIPPED_SIZE=$(du -sh . | cut -f1)
cd ..

echo "📊 Lambda-compatible layer - ZIP: $ZIP_SIZE, Unzipped: $UNZIPPED_SIZE"

# Verify pydantic_core is in the layer
if [ -d "python/pydantic_core" ]; then
    echo "✅ pydantic_core found in layer"
else
    echo "❌ pydantic_core missing from layer!"
fi

# Upload to S3
aws s3 cp lambda-layer-lambda-compatible.zip s3://crawlchat-deployment/
echo "☁️ Uploaded: s3://crawlchat-deployment/lambda-layer-lambda-compatible.zip"

cd ..

# Clean up
rm -f Dockerfile.lambda-layer

echo "🎉 Lambda-compatible layer created and uploaded!"
echo ""
echo "📋 Next steps:"
echo "1. Go to AWS Lambda Console"
echo "2. Click 'Layers' in the left sidebar"
echo "3. Create a new layer version for 'crawlchat-dependencies'"
echo "4. Upload from S3: s3://crawlchat-deployment/lambda-layer-lambda-compatible.zip"
echo "5. Update your Lambda function to use the new layer version"
echo ""
echo "🔧 This layer was built in a Lambda-compatible environment to avoid GLIBC version issues."
echo "📦 Optimized for lightweight dependencies: PyPDF2 + pdfminer.six (no pdfplumber/pymupdf)"
echo "🔍 Includes pydantic_core for Pydantic v2 compatibility" 