# ---------- FINAL LAMBDA IMAGE ----------
FROM public.ecr.aws/lambda/python:3.10

# Install system dependencies for web crawling
RUN yum update -y && yum clean all

# Copy requirements file (Docker-specific, excludes local packages)
COPY requirements-docker.txt ${LAMBDA_TASK_ROOT}/requirements.txt
RUN pip install --no-cache-dir -r ${LAMBDA_TASK_ROOT}/requirements.txt

# Copy crawler code
COPY lambda_handler.py ${LAMBDA_TASK_ROOT}/
COPY main.py ${LAMBDA_TASK_ROOT}/
COPY crawler_main.py ${LAMBDA_TASK_ROOT}/
COPY src/ ${LAMBDA_TASK_ROOT}/src/

# Copy centralized UI (from parent directory context)
COPY ../ui/templates/ ${LAMBDA_TASK_ROOT}/templates/
COPY ../ui/static/ ${LAMBDA_TASK_ROOT}/static/

# Lambda handler entry point
CMD ["lambda_handler.handler"]
    