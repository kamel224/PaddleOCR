from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from paddleocr import PaddleOCR
from PIL import Image
import io
import logging
import os

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="PaddleOCR API",
    version="1.0.0",
    description="Chinese OCR Service powered by PaddleOCR"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

ocr_engine = None

def get_ocr():
    global ocr_engine
    if ocr_engine is None:
        logger.info("初始化 PaddleOCR 引擎...")
        ocr_engine = PaddleOCR(
            use_angle_cls=True,
            lang='ch',
            use_gpu=False
        )
        logger.info("PaddleOCR 引擎就緒")
    return ocr_engine

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "service": "PaddleOCR API",
        "version": "1.0.0"
    }

@app.post("/ocr")
async def recognize_text(file: UploadFile = File(...)):
    import time
    start_time = time.time()
    
    try:
        allowed_types = {'image/jpeg', 'image/png', 'image/bmp', 'image/gif'}
        if file.content_type not in allowed_types:
            raise HTTPException(
                status_code=400,
                detail=f"不支持的文件類型: {file.content_type}. 允許: {allowed_types}"
            )
        
        contents = await file.read()
        if len(contents) > 10 * 1024 * 1024:
            raise HTTPException(status_code=413, detail="文件過大（>10MB）")
        
        image = Image.open(io.BytesIO(contents))
        logger.info(f"處理圖像: {image.size}, 格式: {image.format}")
        
        ocr = get_ocr()
        result = ocr.ocr(image, cls=True)
        
        formatted_result = []
        if result:
            for line in result:
                if line:
                    for word_info in line:
                        try:
                            formatted_result.append({
                                "text": word_info[1][0],
                                "confidence": float(word_info[1][1]),
                                "bbox": [[float(p[0]), float(p[1])] for p in word_info[0]]
                            })
                        except (IndexError, TypeError) as e:
                            logger.warning(f"解析單詞信息失敗: {e}")
                            continue
        
        processing_time = (time.time() - start_time) * 1000
        
        return JSONResponse({
            "success": True,
            "data": formatted_result,
            "count": len(formatted_result),
            "processing_time_ms": round(processing_time, 2)
        })
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"OCR 處理錯誤: {str(e)}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "error": f"OCR 處理失敗: {str(e)}"
            }
        )

@app.post("/batch_ocr")
async def batch_recognize(files: list[UploadFile] = File(...)):
    results = []
    for file in files:
        response = await recognize_text(file)
        results.append({
            "filename": file.filename,
            "result": response
        })
    return {"batch_results": results}

@app.get("/")
async def root():
    return {
        "name": "PaddleOCR API",
        "version": "1.0.0",
        "endpoints": {
            "GET /health": "健康檢查",
            "POST /ocr": "單張圖像OCR識別",
            "POST /batch_ocr": "批量OCR識別",
            "GET /docs": "Swagger文檔"
        },
        "docs_url": "/docs"
    }

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
