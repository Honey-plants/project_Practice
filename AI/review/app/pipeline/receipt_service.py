import json
from .receipt_preprocess import preprocess_image
from .receipt_parser import build_receipt_json
from .ocr_model import ocr_model
from .receipt_translation import translate_ko2en



def get_ocr():
    return ocr_model

def process_receipt_ocr(image_bytes: bytes) -> dict:
    #모델 불러오기
    ocr = get_ocr()
    # img = preprocess_size(image_bytes)
    #이미지 전처리
    img = preprocess_image(image_bytes)

    #OCR 돌리기
    result = ocr.predict(img)

    if not result or not result[0]:
        return {"error": "No text detected"}

    #OCR 데이터 처리하기
    receipt = build_receipt_json(result[0])
    #
    # draw_ocr_boxes(
    #     image=img,
    #     ocr_result=result[0],
    #     save_path="../ocr_bbox.png"
    # )
    with open("receipt_result.json", "w", encoding="utf-8") as f:

        json.dump(receipt, f, ensure_ascii=False, indent=2)

    return receipt

