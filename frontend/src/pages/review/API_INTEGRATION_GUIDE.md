# Review API 연동 가이드

## 📋 개요
이 문서는 `ReviewCreate.jsx`를 백엔드 API와 연동하는 방법을 설명합니다.
현재는 STUB 함수를 사용하여 임시로 작동하며, 백엔드 API가 완성되면 아래 단계를 따라 실제 API로 교체하면 됩니다.

---

## 🔧 연동 단계

### 1단계: Backend API 완성 확인

다음 엔드포인트들이 완성되어야 합니다:

#### 1.1 영수증 업로드 및 OCR
- **현재 상태**: `backend/app/features/review/router.py`에 `/review/upload` 엔드포인트 존재 (line 11-38)
- **확인 사항**:
  - OCR 처리 로직이 구현되었는지 확인 (현재 주석 처리: line 20-21)
  - 응답 형식이 다음과 같은지 확인:
    ```json
    {
      "store_name": "가게 이름",
      "store_en": "Store Name EN",
      "address": "주소",
      "menu_name": "메뉴명"
    }
    ```

#### 1.2 리뷰 생성
- **현재 상태**: `backend/app/features/review/router.py`에 주석 처리된 코드 존재 (line 50-60)
- **필요 작업**: 주석 해제 및 활성화
- **엔드포인트**: `POST /review`
- **요청 body**:
  ```json
  {
    "review_title": "리뷰 제목",
    "review_content": "리뷰 내용",
    "rating": 5,
    "location": "주소",
    "receipt_menu_name": "메뉴명" // 선택적
  }
  ```
- **응답**:
  ```json
  {
    "review_id": 123,
    "review_title": "리뷰 제목",
    ...
  }
  ```

#### 1.3 리뷰 이미지 업로드
- **현재 상태**: 아직 구현되지 않음
- **필요 작업**: 새로운 엔드포인트 생성
- **엔드포인트**: `POST /review/{review_id}/images`
- **요청**: `multipart/form-data` 형식으로 이미지 파일 전송
- **응답**: 업로드 성공 여부

---

### 2단계: API Router 등록

`backend/app/api_router.py` 파일 수정:

```python
# Line 12: 주석 해제
from .features.review.router import router as review_router

# Line 30: 주석 해제
api_router.include_router(review_router)
```

---

### 3단계: Frontend 코드 수정

#### 3.1 `ReviewCreate.jsx` 수정

**파일 위치**: `frontend/src/pages/review/ReviewCreate.jsx`

##### Step 1: import 주석 해제 (line 5-8)
```javascript
// 현재 (주석 처리됨):
// import { uploadReceipt, uploadReviewImages } from "../../api/reviewApi";

// 변경 후 (주석 해제):
import { uploadReceipt, uploadReviewImages } from "../../api/reviewApi";
```

##### Step 2: STUB 함수 삭제 또는 주석 처리 (line 27-68)
다음 함수들을 삭제하거나 주석 처리:
- `uploadReceiptStub` (line 37-51)
- `uploadReviewImagesStub` (line 62-68)

##### Step 3: `runReceiptOCR` 함수 수정 (line 103)
```javascript
// 현재:
const data = await uploadReceiptStub(resizedFile);

// 변경 후:
const data = await uploadReceipt(resizedFile);
```

##### Step 4: `submitReview` 함수 수정 (line 197)
```javascript
// 현재:
await uploadReviewImagesStub(reviewId, reviewImages.slice(0, 3));

// 변경 후:
await uploadReviewImages(reviewId, reviewImages.slice(0, 3));
```

---

#### 3.2 `reviewApi.js` 확인

**파일 위치**: `frontend/src/api/reviewApi.js`

이미 `uploadReceipt`와 `uploadReviewImages` 함수가 준비되어 있습니다.
백엔드 엔드포인트가 다음과 다를 경우 수정이 필요합니다:

##### `uploadReceipt` 함수 (line 35-63)
- **현재 URL**: `/review/upload`
- **백엔드 URL이 다르면 수정**:
  ```javascript
  // line 54-55
  const response = await api.post("/review/upload", formData, {
  ```
  를 실제 엔드포인트로 변경

##### `uploadReviewImages` 함수 (line 80-113)
- **현재 URL**: `/review/{reviewId}/images`
- **백엔드 URL이 다르면 수정**:
  ```javascript
  // line 104-105
  const response = await api.post(`/review/${reviewId}/images`, formData, {
  ```
  를 실제 엔드포인트로 변경

- **FormData 필드명 확인**:
  ```javascript
  // line 96-99
  files.forEach((file, index) => {
    formData.append("images", file);  // ← 백엔드가 기대하는 필드명으로 변경
  });
  ```
  백엔드가 `"image"` 또는 `"files"` 등 다른 필드명을 기대하면 여기를 수정

---

## 🧪 테스트 순서

### 1. 백엔드 API 테스트
```bash
# 백엔드 서버 실행 후
curl -X POST http://localhost:8000/review/upload \
  -F "image=@test.jpg" \
  -F "type=review"

curl -X POST http://localhost:8000/review \
  -H "Content-Type: application/json" \
  -d '{"review_title":"테스트","review_content":"내용","rating":5}'
```

### 2. 프론트엔드 통합 테스트
1. 영수증 이미지 업로드
2. OCR 결과 확인
3. Confirm 버튼 클릭
4. 리뷰 작성 (제목, 내용, 평점, 이미지 0~3개)
5. Create Review 버튼 클릭
6. 콘솔 로그 확인

---

## 📝 체크리스트

### Backend
- [ ] `/review/upload` 엔드포인트 OCR 로직 완성
- [ ] `/review` POST 엔드포인트 주석 해제 및 활성화
- [ ] `/review/{review_id}/images` 엔드포인트 생성
- [ ] `api_router.py`에 review_router 등록

### Frontend
- [ ] `ReviewCreate.jsx`의 import 주석 해제
- [ ] STUB 함수 삭제/주석 처리
- [ ] `runReceiptOCR`에서 `uploadReceipt` 사용
- [ ] `submitReview`에서 `uploadReviewImages` 사용
- [ ] `reviewApi.js`의 엔드포인트 URL 확인 및 수정
- [ ] FormData 필드명 확인

---

## 🔍 주요 변경 포인트 요약

| 파일 | 라인 | 현재 코드 | 변경 후 코드 |
|------|------|-----------|--------------|
| `ReviewCreate.jsx` | 8 | `// import { uploadReceipt, ... }` | `import { uploadReceipt, ... }` |
| `ReviewCreate.jsx` | 103 | `uploadReceiptStub(resizedFile)` | `uploadReceipt(resizedFile)` |
| `ReviewCreate.jsx` | 197 | `uploadReviewImagesStub(...)` | `uploadReviewImages(...)` |
| `reviewApi.js` | 54 | `/review/upload` | 실제 엔드포인트로 변경 (필요시) |
| `reviewApi.js` | 104 | `/review/${reviewId}/images` | 실제 엔드포인트로 변경 (필요시) |
| `api_router.py` | 12 | `# from .features.review...` | `from .features.review...` |
| `api_router.py` | 30 | `# api_router.include_router...` | `api_router.include_router...` |

---

## 💾 백업 파일

원본 `ReviewCreate.jsx` 파일은 다음 위치에 백업되어 있습니다:
```
frontend/src/pages/review/ReviewCreate.jsx.backup
```

문제 발생 시 이 파일을 참고하거나 복구할 수 있습니다.

---

## 🎯 Context 연동 확인

현재 `ReviewCreate.jsx`는 다음과 같이 Context와 연동되어 있습니다:

```javascript
// line 19: Context에서 reviewActions 가져오기
const { reviewActions } = useContext(ReviewContext);

// line 188: Context의 create 함수 사용
const result = await reviewActions.create(payload);
```

이 부분은 **변경하지 않아도** 됩니다. Context의 `create` 함수는 자동으로 `ReviewAPI.create`를 호출하므로, 백엔드 API가 완성되면 자동으로 연동됩니다.

---

## ❓ 문제 해결

### Q: API 호출이 실패합니다
- `axiosInstance.js`의 `BASE_URL` 확인 (현재 빈 문자열)
- 백엔드 서버가 실행 중인지 확인
- CORS 설정 확인
- 브라우저 콘솔에서 네트워크 탭 확인

### Q: OCR 결과 형식이 다릅니다
- `reviewApi.js`의 `uploadReceipt` 함수에서 응답 데이터 파싱 로직 추가
- 예: `return response.data.ocr_result`

### Q: 리뷰 이미지 업로드가 안 됩니다
- `reviewApi.js`의 `uploadReviewImages` 함수에서 FormData 필드명 확인
- 백엔드가 기대하는 필드명과 일치하는지 확인

---

## 📞 연락처

문제가 발생하거나 추가 도움이 필요하면 개발팀에 문의하세요.
