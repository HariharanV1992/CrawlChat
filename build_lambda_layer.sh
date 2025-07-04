#!/bin/bash

echo "🔨 Building Lambda Layer with updated dependencies"
echo "=================================================="

# Clean up any previous build
echo "🧹 Cleaning up previous build..."
rm -rf python lambda-layer-complete.zip

# Create a temporary Dockerfile for building the layer
echo "🐳 Creating Docker build environment..."
cat > Dockerfile.layer << 'EOF'
FROM public.ecr.aws/lambda/python:3.10

# Copy requirements file (using the Lambda-specific one)
COPY requirements-lambda.txt requirements.txt

# Install dependencies to python/ directory
RUN pip install --upgrade pip && \
    pip install -r requirements.txt -t python/

# Create the layer zip
RUN cd /tmp && zip -r lambda-layer-complete.zip python/

# The zip will be in /tmp/lambda-layer-complete.zip
EOF

# Build the Docker image
echo "🔨 Building Docker image..."
docker build -f Dockerfile.layer -t lambda-layer-builder .

# Extract the layer zip from the container
echo "📦 Extracting layer zip..."
CONTAINER_ID=$(docker create lambda-layer-builder)
docker cp $CONTAINER_ID:/tmp/lambda-layer-complete.zip ./lambda-layer-complete.zip
docker rm $CONTAINER_ID

# Clean up Docker artifacts
echo "🧹 Cleaning up Docker artifacts..."
docker rmi lambda-layer-builder
rm -f Dockerfile.layer

# Verify the zip was created
if [ -f lambda-layer-complete.zip ]; then
    echo "✅ Lambda layer created successfully!"
    echo "📊 Layer size: $(du -h lambda-layer-complete.zip | cut -f1)"
    echo "📁 Contents:"
    unzip -l lambda-layer-complete.zip | head -20
else
    echo "❌ Failed to create lambda layer!"
    exit 1
fi

echo ""
echo "🎉 Lambda layer build complete!"
echo "📋 Next steps:"
echo "   1. Upload to S3: aws s3 cp lambda-layer-complete.zip s3://YOUR_BUCKET/lambda-layer-complete.zip"
echo "   2. Update layer: bash update_lambda_layer.sh" 