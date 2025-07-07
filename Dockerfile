# ---------- FINAL LAMBDA IMAGE ----------
FROM public.ecr.aws/lambda/python:3.10

# Install system dependencies for PDF processing
RUN yum update -y && yum clean all

# Copy your app code
COPY requirements-lambda.txt ${LAMBDA_TASK_ROOT}/requirements.txt
RUN pip install --no-cache-dir -r ${LAMBDA_TASK_ROOT}/requirements.txt

# Copy the main application files
COPY lambda_handler.py ${LAMBDA_TASK_ROOT}/
COPY main.py ${LAMBDA_TASK_ROOT}/
COPY src/ ${LAMBDA_TASK_ROOT}/src/
COPY templates/ ${LAMBDA_TASK_ROOT}/templates/
COPY static/ ${LAMBDA_TASK_ROOT}/static/

# Copy the S3-based PDF handler for testing
COPY lambda_handler_s3.py ${LAMBDA_TASK_ROOT}/

# Create data directories
RUN mkdir -p ${LAMBDA_TASK_ROOT}/data/uploads
RUN mkdir -p ${LAMBDA_TASK_ROOT}/data/processed
RUN mkdir -p ${LAMBDA_TASK_ROOT}/data/temp

# Set proper permissions
RUN chmod -R 755 ${LAMBDA_TASK_ROOT}

# Lambda handler entry point
CMD ["lambda_handler.handler"]
    