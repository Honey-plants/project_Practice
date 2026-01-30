import { useState, useContext } from "react";
import { useNavigate } from "react-router-dom";
import { resizeAndCompressImage } from "../../contents/imageProcessor";
import { ReviewContext } from "../../context/ReviewContext";

// ✅ API 연동 준비:
// - 나중에 backend/app/features/review/router.py가 완성되면
// - 아래 주석을 해제하고 실제 API 함수들을 import하세요
// import { uploadReceipt, uploadReviewImages } from "../../api/reviewApi";

export default function ReviewWritePage() {
  const navigate = useNavigate();
  const [step, setStep] = useState("upload"); // upload -> confirm -> write -> done
  const [receipt, setReceipt] = useState(null);
  const [formData, setFormData] = useState({ title: "", content: "", rating: "" });
  const [imageFile, setImageFile] = useState(null);      // 영수증 이미지
  const [loading, setLoading] = useState(false);
  const [reviewImages, setReviewImages] = useState([]);  // 리뷰 이미지 (0~3)

  // ✅ Context에서 reviewActions 가져오기
  const { reviewActions } = useContext(ReviewContext);

  // =========================
  // ✅ STUB (임시 API 대체)
  // - 현재 페이지 단독 테스트용
  // - 나중에 API 완성되면 주석 해제된 실제 API로 교체
  // =========================

  /**
   * ✅ uploadReceipt STUB
   * - 실제론 서버에 영수증 이미지를 업로드하고 OCR 결과(가게명/주소/메뉴명 등)를 받아야 함
   * - 지금은 "OCR 된 것처럼" 더미 데이터를 반환
   *
   * 🔧 API 연동 시 변경 포인트:
   * 1. 이 함수를 삭제하거나 주석 처리
   * 2. 상단의 import 주석 해제: import { uploadReceipt, ... } from "../../api/reviewApi"
   * 3. runReceiptOCR 함수 내에서 uploadReceiptStub -> uploadReceipt로 교체
   */
  async function uploadReceiptStub(file) {
    console.log("[STUB] uploadReceipt called with:", {
      name: file?.name,
      type: file?.type,
      size: file?.size,
    });

    // 서버 응답 형태를 최대한 비슷하게 흉내냄
    return {
      store_name: "Sample Store",
      store_en: "Sample Store EN",
      address: "Seoul, Korea",
      menu_name: "김밥, 라면", // ✅ 메뉴명 확인용
    };
  }

  /**
   * ✅ uploadReviewImages STUB
   * - 실제론 reviewId + 이미지 파일들을 서버에 업로드해야 함
   *
   * 🔧 API 연동 시 변경 포인트:
   * 1. 이 함수를 삭제하거나 주석 처리
   * 2. 상단의 import 주석 해제: import { ..., uploadReviewImages } from "../../api/reviewApi"
   * 3. submitReview 함수 내에서 uploadReviewImagesStub -> uploadReviewImages로 교체
   */
  async function uploadReviewImagesStub(reviewId, files) {
    console.log("[STUB] uploadReviewImages called:", {
      reviewId,
      files: (files || []).map((f) => ({ name: f.name, type: f.type, size: f.size })),
    });
    return { ok: true };
  }

  // =========================
  // ✅ 사용자 입력값 저장 (제목, 내용, 평점)
  // =========================
  const onChange = (e) => {
    const { name, value } = e.target;
    setFormData((prev) => ({ ...prev, [name]: value }));
  };

  // =========================
  // ✅ 영수증 OCR 실행
  // - step === "upload"일 때만 실행됨 (기존 흐름 유지)
  //
  // 🔧 API 연동 시 변경 포인트:
  // - uploadReceiptStub를 실제 uploadReceipt로 교체
  // =========================
  const runReceiptOCR = async () => {
    if (!imageFile) {
      alert("이미지를 선택해주세요");
      return;
    }
    setLoading(true);

    try {
      // 이미지 리사이즈 (기존 코드 유지)
      const resizedBlob = await resizeAndCompressImage(imageFile, 1024);
      const resizedFile = new File([resizedBlob], imageFile.name, { type: "image/jpeg" });

      console.log("original:", imageFile.size);
      console.log("resized:", resizedFile.size);

      // ✅ 현재는 STUB 사용 (API 미완성)
      // 🔧 API 연동 후에는 다음과 같이 변경:
      // const data = await uploadReceipt(resizedFile);
      const data = await uploadReceiptStub(resizedFile);

      // ✅ OCR 결과 수신 후 confirm 단계로 이동
      setReceipt(data);
      setStep("confirm");
    } catch (err) {
      console.error(err);
      alert(err?.message || "영수증 분석 실패");
    } finally {
      setLoading(false);
    }
  };

  // =========================
  // ✅ 리뷰 이미지 선택 (0~3개 제한)
  // =========================
  const onSelectReviewImages = (e) => {
    const files = Array.from(e.target.files || []);
    if (files.length > 3) {
      alert("리뷰 이미지는 최대 3개까지 선택 가능합니다. (앞에서 3개만 적용)");
    }
    const limited = files.slice(0, 3);
    setReviewImages(limited);

    console.log("[SELECTED REVIEW IMAGES]", limited.map((f) => ({
      name: f.name,
      type: f.type,
      size: f.size,
    })));
  };

  // =========================
  // ✅ 리뷰 등록 (저장) - Context의 create 함수 사용
  // - 저장 시 console.log로 payload/이미지/receipt가 제대로 들어왔는지 최종 확인
  //
  // 🔧 API 연동 시 변경 포인트:
  // 1. reviewActions.create()는 그대로 사용 (Context가 API를 호출함)
  // 2. uploadReviewImagesStub를 실제 uploadReviewImages로 교체
  // =========================
  const submitReview = async () => {
    // ✅ write 단계에서만 저장 가능 (흐름 보호)
    if (step !== "write") {
      alert("영수증 확인 후 Confirm을 눌러 리뷰 작성 단계로 이동해주세요.");
      return;
    }

    // ✅ 입력 검증 (타이틀/내용/별점)
    const title = formData.title.trim();
    const content = formData.content.trim();
    const ratingNum =
      formData.rating === "" || formData.rating == null ? null : Number(formData.rating);

    if (!title) return alert("리뷰 제목을 입력해주세요.");
    if (!content) return alert("리뷰 내용을 입력해주세요.");
    if (ratingNum == null || Number.isNaN(ratingNum)) return alert("별점을 입력해주세요.");
    if (ratingNum < 1 || ratingNum > 5) return alert("별점은 1~5 사이로 입력해주세요.");

    const payload = {
      review_title: title,
      review_content: content,
      rating: ratingNum,
      // receipt가 없을 수도 있으니 안전하게
      location: receipt?.address || null,
      // 나중에 API 연결 시 도움이 되도록 receipt의 menu도 같이 확인만 해두기
      // (백엔드 스키마에 넣을지 말지는 라우터 완성 후 결정)
      receipt_menu_name: receipt?.menu_name || null,
    };

    // ✅ 최종 확인용 로그 (요구사항 핵심)
    console.log("====== [FINAL SUBMIT CHECK] ======");
    console.log("[step]", step);
    console.log("[payload]", payload);
    console.log("[receipt]", receipt);
    console.log(
      "[reviewImages meta]",
      (reviewImages || []).slice(0, 3).map((f) => ({ name: f.name, type: f.type, size: f.size }))
    );
    console.log("==================================");

    setLoading(true);
    try {
      // ✅ Context의 create 함수 호출 (ReviewAPI.create를 사용)
      // 🔧 API 연동 후:
      // - reviewActions.create()는 그대로 사용
      // - ReviewAPI.create가 backend의 POST /review를 호출하게 됨
      const result = await reviewActions.create(payload);

      // API 응답에서 review_id 추출
      const reviewId = result.review_id || result.id;

      // ✅ 이미지 업로드는 있을 때만 (0개 가능 / 최대 3개)
      // 🔧 API 연동 후:
      // - uploadReviewImagesStub를 uploadReviewImages로 교체
      if (reviewImages.length > 0) {
        await uploadReviewImagesStub(reviewId, reviewImages.slice(0, 3));
        // 🔧 API 연동 후에는:
        // await uploadReviewImages(reviewId, reviewImages.slice(0, 3));
      }

      // 리뷰 생성 완료 후 리스트로 이동
      alert("리뷰가 성공적으로 작성되었습니다!");
      navigate("/review");
    } catch (err) {
      console.error(err);
      alert(err?.message || "Creating review failed.");
    } finally {
      setLoading(false);
    }
  };

  // ✅ confirm 버튼 눌렀을 때 write 단계로 넘어가면서 "입력창 활성화" 조건 충족
  const confirmReceipt = () => {
    setStep("write");
  };

  // ✅ write 단계에서만 입력 가능하도록 disabled 조건 부여
  const isWriteEnabled = step === "write";

  return (
    <div className="reviewWritePage">
      <h1>Create Review</h1>

      {/* ✅ 리뷰 타이틀은 "Confirm 후(write 단계)"에만 활성화 */}
      <label>Review Title: </label>
      <input
        name="title"
        type="text"
        placeholder="Enter review title"
        value={formData.title}
        onChange={onChange}
        disabled={!isWriteEnabled}
      />

      {/* 1. Upload & Detect */}
      <h2>1. Upload Receipt</h2>
      <input
        type="file"
        accept="image/*"
        disabled={step !== "upload"}
        onChange={(e) => setImageFile(e.target.files?.[0] || null)}
      />
      <button disabled={!imageFile || step !== "upload" || loading} onClick={runReceiptOCR}>
        {loading ? "분석 중..." : "업로드"}
      </button>

      {/* 2. Receipt 확인 */}
      {receipt && (
        <div style={{ marginTop: 20, opacity: step === "upload" ? 0.5 : 1 }}>
          <h3>영수증 확인</h3>
          <div>
            <p>
              Store name: {receipt.store_name}/ {receipt.store_en}
            </p>
            <p>Address: {receipt.address}</p>

            {/* ✅ 메뉴명 확인 */}
            <p>Menu: {receipt.menu_name}</p>

            {step === "confirm" && (
              <button onClick={confirmReceipt}>Confirm Receipt Detail</button>
            )}
          </div>
        </div>
      )}

      {/* 3. Review 작성 */}
      {/* ✅ Confirm(=write 단계) 이후에만 표시/활성화 */}
      {step === "write" && (
        <div style={{ marginTop: 20 }}>
          {/* ✅ 리뷰 이미지 업로드 (0~3개) */}
          <input type="file" accept="image/*" multiple onChange={onSelectReviewImages} />
          <div style={{ fontSize: 12, opacity: 0.8 }}>
            선택된 이미지: {reviewImages.length}개 (최대 3개)
          </div>

          <h3>Review Content</h3>
          <textarea
            name="content"
            rows={5}
            value={formData.content}
            onChange={onChange}
            placeholder="Write Review"
            style={{ width: "100%" }}
          />

          <div>
            <label>Rating: </label>
            <input
              name="rating"
              type="number"
              min={1}
              max={5}
              value={formData.rating}
              onChange={onChange}
            />
          </div>

          <button disabled={loading} onClick={submitReview}>
            {loading ? "저장 중..." : "Create Review"}
          </button>
        </div>
      )}
    </div>
  );
}
