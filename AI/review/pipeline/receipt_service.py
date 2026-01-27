
# AI/review/pipeline/receipt_service.py

import json
from .receipt_preprocess import preprocess_image
from .receipt_parser import build_receipt_json
from .ocr_model import get_ocr_model
from .receipt_translation import translate_ko2en  # 사용 안 하면 제거 가능

def process_receipt_ocr(image_bytes: bytes) -> dict:
    # 1) 이미지 전처리
    img = preprocess_image(image_bytes)

    # 2) OCR 모델 Lazy 로딩
    ocr = get_ocr_model()

    # 3) OCR 수행

    result = ocr.predict(img)

    if not result or not result[0]:
        return {"error": "No text detected"}


    # 4) 결과 파싱
    receipt = build_receipt_json(result[0])

    # (옵션) 디버그 저장: 컨테이너 환경에서는 파일 쓰기 비권장
    # 필요하면 /tmp 등에 쓰거나 기능 플래그로 제어 권장
    # with open("/tmp/receipt_result.json", "w", encoding="utf-8") as f:
    #     json.dump(receipt, f, ensure_ascii=False, indent=2)

    return receipt
