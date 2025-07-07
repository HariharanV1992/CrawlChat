# ---------- FINAL LAMBDA IMAGE ----------
FROM public.ecr.aws/lambda/python:3.10

# Install system dependencies for web crawling
RUN yum update -y && yum clean all

# Copy requirements file
COPY requirements.txt ${LAMBDA_TASK_ROOT}/requirements.txt
RUN pip install --no-cache-dir -r ${LAMBDA_TASK_ROOT}/requirements.txt

# Copy crawler code
COPY lambda_handler.py ${LAMBDA_TASK_ROOT}/
COPY crawler_main.py ${LAMBDA_TASK_ROOT}/
COPY src/ ${LAMBDA_TASK_ROOT}/src/

# Lambda handler entry point
CMD ["lambda_handler.handler"]
    