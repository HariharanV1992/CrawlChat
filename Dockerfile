# ---------- BUILD STAGE ----------
    FROM amazonlinux:2 AS build

    # Install build dependencies
    RUN yum update -y && \
        yum install -y \
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
        && yum clean all && \
        rm -rf /var/cache/yum
    
    WORKDIR /tmp
    
    # Install Leptonica from package manager (more reliable for Lambda)
RUN yum install -y epel-release && \
    yum install -y leptonica-devel && \
    yum clean all && rm -rf /var/cache/yum
    
    # Build Tesseract
    RUN git clone --branch 5.3.3 --depth 1 https://github.com/tesseract-ocr/tesseract.git && \
        cd tesseract && \
        ./autogen.sh && \
        ./configure --prefix=/usr/local && \
        make && make install && \
        ldconfig && \
        cd /tmp && rm -rf tesseract
    
    # ---------- FINAL LAMBDA IMAGE ----------
    FROM public.ecr.aws/lambda/python:3.10
    
    # Install runtime dependencies
    RUN yum update -y && yum install -y \
        poppler-utils \
        && yum clean all && rm -rf /var/cache/yum
    
    # Copy Tesseract + Leptonica from build stage
    COPY --from=build /usr/local /usr/local
    
    # Download Tesseract English language data
    RUN mkdir -p /usr/local/share/tessdata && \
        wget -O /usr/local/share/tessdata/eng.traineddata https://github.com/tesseract-ocr/tessdata/raw/main/eng.traineddata
    
    # Copy your app code
    COPY requirements.txt ${LAMBDA_TASK_ROOT}/
    RUN pip install --no-cache-dir -r ${LAMBDA_TASK_ROOT}/requirements.txt
    
    COPY lambda_handler.py ${LAMBDA_TASK_ROOT}/
    COPY main.py ${LAMBDA_TASK_ROOT}/
    COPY src/ ${LAMBDA_TASK_ROOT}/src/
    COPY templates/ ${LAMBDA_TASK_ROOT}/templates/
    COPY static/ ${LAMBDA_TASK_ROOT}/static/
    
    CMD ["lambda_handler.handler"]
    