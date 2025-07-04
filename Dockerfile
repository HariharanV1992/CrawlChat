# ---------- BUILD STAGE ----------
FROM tesseractshadow/tesseract4re AS tesseract

# ---------- FINAL LAMBDA IMAGE ----------
FROM public.ecr.aws/lambda/python:3.10

# Install runtime dependencies
RUN yum update -y && \
    yum install -y poppler-utils && \
    yum clean all && rm -rf /var/cache/yum

# Copy Tesseract + Leptonica from the tesseractshadow image
COPY --from=tesseract /usr/local /usr/local
COPY --from=tesseract /usr/share/tessdata /usr/local/share/tessdata

# Add Tesseract to PATH and library paths
ENV PATH="/usr/local/bin:${PATH}"
ENV LD_LIBRARY_PATH="/usr/local/lib:${LD_LIBRARY_PATH}"
    
# Tesseract English language data is already included from tesseractshadow image
    
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
    