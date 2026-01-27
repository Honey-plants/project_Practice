import base64
import traceback
from fastapi import APIRouter, UploadFile, File, HTTPException
from backend.app.core.job_queue import connect_redis, enqueue_task, utc_now_iso

# from AI.review.pipeline.receipt_service import process_receipt_ocr  <-- REMOVED

router = APIRouter(prefix="/upload", tags=["upload"])

@router.post("/receipt")
async def receipt_ocr(image: UploadFile = File(...)):
    """
    영수증 OCR 요청 엔드포인트.
    
    기존: 동기 처리 (process_receipt_ocr)
    변경: 비동기 Job Enqueue (Redis)
    
    이미지 파일을 Base64로 인코딩하여 Redis Payload에 태워 보냅니다.
    (주의: 상용 환경에서는 S3/MinIO 업로드 후 URL을 넘기는 것이 권장됩니다.)
    """
    try:
        print("[DEBUG] endpoint hit (Async Job)")
        print("[DEBUG] filename:", image.filename)
        print("[DEBUG] content_type:", image.content_type)

        contents = await image.read()
        print("[DEBUG] image bytes:", len(contents))
        
        # Base64 Encoding
        encoded_image = base64.b64encode(contents).decode("utf-8")
        
        # Redis 연결
        r = connect_redis()
        
        # Job Enqueue
        payload = {
            "filename": image.filename,
            "content_type": image.content_type,
            "image_base64": encoded_image
        }
        
        job_id = enqueue_task(r, task="receipt_ocr", payload=payload)
        
        return {
            "message": "Job enqueued successfully",
            "job_id": job_id,
            "status": "PENDING",
            "queued_at": utc_now_iso()
        }

    except Exception as e:
        print("🔥 OCR ENQUEUE ERROR 🔥")
        traceback.print_exc()

        raise HTTPException(
            status_code=500,
            detail=str(e),
        )
