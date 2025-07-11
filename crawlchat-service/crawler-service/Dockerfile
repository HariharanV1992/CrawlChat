# ---------- CRAWLER SERVICE LAMBDA IMAGE ----------
FROM public.ecr.aws/lambda/python:3.10

# Install system dependencies if needed (optional)
# RUN yum update -y && yum install -y ... && yum clean all

# Copy the entire src directory
COPY src/ ${LAMBDA_TASK_ROOT}/src/

# Set PYTHONPATH so 'src' is importable
ENV PYTHONPATH="${LAMBDA_TASK_ROOT}/src:${PYTHONPATH}"

# Install requirements if needed
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the lambda handler
COPY lambda_handler.py ${LAMBDA_TASK_ROOT}/

# Set the handler
CMD ["lambda_handler.lambda_handler"] 