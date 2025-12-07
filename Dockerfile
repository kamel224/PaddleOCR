FROM python:3.9-slim-bullseye

WORKDIR /app

# 安裝系統依賴
RUN apt-get update && apt-get install -y \
    build-essential \
    gcc \
    g++ \
    gfortran \
    libopenblas-dev \
    liblapack-dev \
    wget \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# 複製PaddleOCR倉庫
COPY . /app

# 創建requirements.txt（使用官方PyPI）
RUN cat > /app/requirements.txt << 'EOF'
paddlepaddle==2.5.1
paddleocr==2.8.1
fastapi==0.95.1
uvicorn==0.21.0
python-multipart==0.0.6
pillow==10.0.0
numpy==1.24.3
opencv-python==4.8.0.76
pyyaml==6.0
scipy==1.11.1
scikit-image==0.21.0
shapely==2.0.1
imgaug==0.4.0
pyclipper==1.3.0.post5
lmdb==1.4.1
tqdm==4.65.0
visualdl==2.5.3
openpyxl==3.1.2
easydict==1.9
onnx==1.14.1
onnxruntime==1.16.0
PDF2Image==1.16.3
pytesseract==0.3.10
cryptography==41.0.3
requests==2.31.0
pydantic==2.0.3
EOF

# 安裝Python依賴（使用官方PyPI，添加重試和超時）
RUN pip install --upgrade pip setuptools wheel && \
    pip install -r /app/requirements.txt \
    --retries 5 \
    --timeout 120 \
    || pip install -r /app/requirements.txt \
    --retries 5 \
    --timeout 120

# 複製API服務腳本
COPY api.py /app/api.py

EXPOSE 8000

# 健康檢查
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')" || exit 1

# 啟動API
CMD ["python", "-m", "uvicorn", "api:app", "--host", "0.0.0.0", "--port", "8000"]
