# ---------- FINAL LAMBDA IMAGE ----------
FROM public.ecr.aws/lambda/python:3.10

# Install system dependencies for PDF processing
RUN yum update -y && yum clean all

# Copy your app code
COPY lambda-service/requirements.txt ${LAMBDA_TASK_ROOT}/requirements.txt
RUN pip install --no-cache-dir -r ${LAMBDA_TASK_ROOT}/requirements.txt

# Copy the common package
COPY common/ ${LAMBDA_TASK_ROOT}/common/

# Copy lambda service files
COPY lambda-service/lambda_handler.py ${LAMBDA_TASK_ROOT}/
COPY lambda-service/main.py ${LAMBDA_TASK_ROOT}/
COPY lambda-service/src/ ${LAMBDA_TASK_ROOT}/src/
COPY lambda-service/templates/ ${LAMBDA_TASK_ROOT}/templates/
COPY lambda-service/static/ ${LAMBDA_TASK_ROOT}/static/

# Lambda handler entry point
CMD ["lambda_handler.handler"]
    