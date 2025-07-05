# ---------- FINAL LAMBDA IMAGE ----------
FROM public.ecr.aws/lambda/python:3.10

# Install system dependencies including Tesseract
RUN yum update -y && \
    yum install -y \
    tesseract \
    tesseract-langpack-eng \
    poppler-utils \
    && yum clean all

# Copy your app code
COPY requirements.txt ${LAMBDA_TASK_ROOT}/
RUN pip install --no-cache-dir -r ${LAMBDA_TASK_ROOT}/requirements.txt

COPY lambda_handler.py ${LAMBDA_TASK_ROOT}/
COPY main.py ${LAMBDA_TASK_ROOT}/
COPY src/ ${LAMBDA_TASK_ROOT}/src/
COPY templates/ ${LAMBDA_TASK_ROOT}/templates/
COPY static/ ${LAMBDA_TASK_ROOT}/static/

# Lambda handler entry point
CMD ["lambda_handler.handler"]
    