# ---------- FINAL LAMBDA IMAGE ----------
FROM public.ecr.aws/lambda/python:3.10

# Install system dependencies for PDF processing
RUN yum update -y && yum install -y poppler-utils poppler-cpp-devel && yum clean all

# Copy your app code
COPY lambda-service/requirements.txt ${LAMBDA_TASK_ROOT}/requirements.txt
COPY common/ ${LAMBDA_TASK_ROOT}/common/

# Copy only the crawler router (not the entire crawler service)
COPY crawler-service/src/crawler/ ${LAMBDA_TASK_ROOT}/crawler/
ENV PYTHONPATH="${LAMBDA_TASK_ROOT}/common:${LAMBDA_TASK_ROOT}"
RUN pip install --no-cache-dir -r ${LAMBDA_TASK_ROOT}/requirements.txt

# Copy lambda service files
COPY lambda-service/lambda_handler.py ${LAMBDA_TASK_ROOT}/
COPY lambda-service/main.py ${LAMBDA_TASK_ROOT}/

# Copy centralized UI
COPY ui/templates/ ${LAMBDA_TASK_ROOT}/templates/
COPY ui/static/ ${LAMBDA_TASK_ROOT}/static/

# Lambda handler entry point
CMD ["lambda_handler.handler"]
    