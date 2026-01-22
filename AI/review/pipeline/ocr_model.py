from paddleocr import PaddleOCR

print("🔥 Loading OCR model once...")

ocr_model = PaddleOCR(
    lang="korean",
    use_textline_orientation=True,
    use_doc_unwarping=False,
    text_det_limit_side_len=1280,
    text_det_thresh=0.3,
    text_det_box_thresh=0.2,
    text_det_unclip_ratio=1.5,
    enable_mkldnn=False,  # 핵심
)


