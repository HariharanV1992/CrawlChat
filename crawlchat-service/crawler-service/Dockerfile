# ---------- CRAWLER SERVICE LAMBDA IMAGE ----------
FROM public.ecr.aws/lambda/python:3.10

# Install system dependencies for PDF processing
RUN yum update -y && yum install -y poppler-utils poppler-cpp-devel && yum clean all

# Copy requirements and install dependencies
COPY requirements.txt ${LAMBDA_TASK_ROOT}/requirements.txt
RUN pip install --no-cache-dir -r ${LAMBDA_TASK_ROOT}/requirements.txt

# Copy crawler modules
COPY src/crawler/ ${LAMBDA_TASK_ROOT}/src/crawler/

# Copy crawler handler
COPY lambda_handler.py ${LAMBDA_TASK_ROOT}/

# Lambda handler entry point
CMD ["lambda_handler.handler"] 