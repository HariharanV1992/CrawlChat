# ---------- FINAL LAMBDA IMAGE ----------
FROM public.ecr.aws/lambda/python:3.10

# Install system dependencies and build tools
RUN yum update -y && yum install -y \
    gcc \
    gcc-c++ \
    make \
    wget \
    tar \
    git \
    autoconf \
    automake \
    libtool \
    pkgconfig \
    openssl-devel \
    libffi-devel \
    python3-devel \
    libjpeg-devel \
    zlib-devel \
    freetype-devel \
    lcms2-devel \
    libwebp-devel \
    tcl-devel \
    tk-devel \
    poppler-utils \
    poppler-devel \
    libpng-devel \
    libtiff-devel \
    epel-release \
    leptonica-devel \
    && yum clean all && rm -rf /var/cache/yum

WORKDIR /tmp

# Install Tesseract and dependencies from package manager (recommended approach)
RUN yum install -y \
    tesseract \
    tesseract-devel \
    leptonica-devel \
    poppler-utils \
    && yum clean all && rm -rf /var/cache/yum

# Set PATH for Tesseract
ENV PATH="/usr/bin:${PATH}"
ENV TESSDATA_PREFIX="/usr/share/tessdata"

# Download English language data manually
RUN mkdir -p /usr/share/tessdata && \
    wget -O /usr/share/tessdata/eng.traineddata https://github.com/tesseract-ocr/tessdata/raw/main/eng.traineddata

# Set library paths
ENV LD_LIBRARY_PATH="/usr/lib64:${LD_LIBRARY_PATH}"

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
    