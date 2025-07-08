# ---------- FINAL LAMBDA IMAGE ----------
FROM public.ecr.aws/lambda/python:3.10

# Install system dependencies for web crawling and PDF processing
RUN yum update -y && \
    yum install -y poppler-utils poppler-cpp-devel && \
    yum clean all

# Copy common package first (needed for requirements.txt)
COPY common/ ${LAMBDA_TASK_ROOT}/common/

# Copy requirements file (Docker-specific, excludes local packages)
COPY lambda-service/requirements.txt ${LAMBDA_TASK_ROOT}/requirements.txt
RUN pip install --no-cache-dir -r ${LAMBDA_TASK_ROOT}/requirements.txt

# Copy lambda service code (updated with S3 caching)
COPY lambda-service/lambda_handler.py ${LAMBDA_TASK_ROOT}/
COPY lambda-service/main.py ${LAMBDA_TASK_ROOT}/
COPY lambda-service/src/ ${LAMBDA_TASK_ROOT}/src/

# Copy centralized UI
COPY ui/templates/ ${LAMBDA_TASK_ROOT}/templates/
COPY ui/static/ ${LAMBDA_TASK_ROOT}/static/

# Lambda handler entry point
CMD ["lambda_handler.lambda_handler"]
    