FROM python:3.9-slim-bullseye

WORKDIR /app

RUN apt-get update && apt-get install -y \
    build-essential \
    gcc \
    g++ \
    gfortran \
    libopenblas-dev \
    liblapack-dev \
    && rm -rf /var/lib/apt/lists/*

COPY . /app

RUN echo "paddleocr==2.8.1" > requirements.txt && \
    echo "fastapi==0.95.1" >> requirements.txt && \
    echo "uvicorn==0.21.0" >> requirements.txt && \
    echo "python-multipart" >> requirements.txt && \
    echo "pillow" >> requirements.txt

RUN pip install -i https://pypi.tuna.tsinghua.edu.cn/simple \
    -r requirements.txt

COPY api.py /app/api.py

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')" || exit 1

CMD ["python", "-m", "uvicorn", "api:app", "--host", "0.0.0.0", "--port", "8000"]
