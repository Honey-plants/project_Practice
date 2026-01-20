import cv2
import numpy as np

def preprocess_image(image_bytes: bytes) -> np.ndarray:
    img_array = np.frombuffer(image_bytes, np.uint8)
    bgr = cv2.imdecode(img_array, cv2.IMREAD_COLOR)
    bgr = cv2.resize(bgr, None, fx=2.0, fy=2.0, interpolation=cv2.INTER_CUBIC)

    gray = cv2.cvtColor(bgr, cv2.COLOR_BGR2GRAY)

    # 가벼운 노이즈 제거
    gray = cv2.fastNlMeansDenoising(gray, None, h=8)

    # 대비만 살짝
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    gray = clahe.apply(gray)

    # 글자 획만 살짝 강화
    blur = cv2.GaussianBlur(gray, (0, 0), 1.0)
    sharp = cv2.addWeighted(gray, 1.5, blur, -0.5, 0)
    ocr_image = cv2.cvtColor(sharp, cv2.COLOR_GRAY2BGR)

    return ocr_image
