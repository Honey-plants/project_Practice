import React, { useEffect, useRef, useState } from "react";
import { ReviewAPI } from "../../api/reviewApi";
import { useNavigate } from "react-router-dom";
import styles from "./ReviewCreate.module.css";

export default function ReviewCreateInline({ onCreated }) {
  const navigate = useNavigate();
  // Step1
  const [receiptFile, setReceiptFile] = useState(null);
  const [receiptId, setReceiptId] = useState(null);
  const [extracted, setExtracted] = useState(null);
  const [menuConfirmed, setMenuConfirmed] = useState(false);

  // Step2
  const [title, setTitle] = useState("");
  const [content, setContent] = useState("");
  const [rating, setRating] = useState(5);

  //  images: File[]
  const [images, setImages] = useState([]);
  //  preview urls
  const [previewUrls, setPreviewUrls] = useState([]);

  const imageInputRef = useRef(null);

  const [loadingVerify, setLoadingVerify] = useState(false);
  const [loadingCreate, setLoadingCreate] = useState(false);
  const [msg, setMsg] = useState("");
  const [err, setErr] = useState("");

  //  preview url 생성/정리
  useEffect(() => {
    // 기존 url 정리
    previewUrls.forEach((u) => URL.revokeObjectURL(u));
    // 새 url 생성
    const next = images.map((f) => URL.createObjectURL(f));
    setPreviewUrls(next);

    // unmount 시 정리
    return () => {
      next.forEach((u) => URL.revokeObjectURL(u));
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [images]);

  const verify = async () => {
    setErr("");
    setMsg("");
    if (!receiptFile) return setErr("??????????????????");

    setLoadingVerify(true);
    try {
      const r = await ReviewAPI.verifyReceipt(receiptFile);
      const jobId = r.data?.job_id;
      if (!jobId) {
        throw new Error("?????? job_id????? ?????");
      }

      setReceiptId(jobId);
      setExtracted(null);
      setMsg("???????? ???????????????.");

      const jobRes = await ReviewAPI.waitReceiptJob(jobId);
      const status = jobRes?.data?.status;
      if (status === "DONE") {
        setExtracted(jobRes?.data?.extracted || null);
        setMsg("???????? ???. ??????????????.");
      } else {
        const err = jobRes?.data?.error;
        const errMsg = err?.message || err?.detail || JSON.stringify(err || {});
        setErr(`???????? ???: ${errMsg}`);
      }
    } catch (e) {
      setErr(e?.response?.data?.detail || e?.message || "???????? ???");
    } finally {
      setLoadingVerify(false);
    }
  };

  const confirmMenu = () => {
    setMenuConfirmed(true);
    setMsg("메뉴 확인 완료. 리뷰를 작성해주세요.");
  };

  const cancelMenu = () => {
    setReceiptId(null);
    setExtracted(null);
    setReceiptFile(null);
    setMenuConfirmed(false);
    setMsg("");
    setErr("");
  };

  //  이미지 추가(append) + 3장 제한 + input reset
  const onPickImages = (e) => {
    const files = Array.from(e.target.files || []);
    if (!files.length) return;

    setErr("");
    setMsg("");

    setImages((prev) => {
      const merged = [...prev, ...files];
      if (merged.length > 3) {
        setErr("이미지는 최대 3장까지 업로드 가능합니다.");
        return prev; // 기존 유지
      }
      return merged;
    });

    // 같은 파일 다시 선택 가능하도록 input reset
    if (imageInputRef.current) imageInputRef.current.value = "";
  };

  //  개별 삭제
  const removeImage = (idx) => {
    setImages((prev) => prev.filter((_, i) => i !== idx));
  };

  const create = async () => {
    setErr("");
    setMsg("");

    if (!receiptId) return setErr("먼저 영수증 인증을 해줘");
    if (!title.trim()) return setErr("title 입력해줘");
    if (!content.trim()) return setErr("content 입력해줘");
    if (images.length > 3) return setErr("이미지는 최대 3장");

    setLoadingCreate(true);
    try {
      const r = await ReviewAPI.createFromReceipt({
        receipt_id: receiptId,
        title,
        content,
        rating,
        images, //  File[] 그대로
      });

      setMsg("리뷰 생성 완료");

      // 리뷰 페이지로 이동
      navigate("/review");

      onCreated?.(r.data);

      // 초기화
      setReceiptFile(null);
      setReceiptId(null);
      setExtracted(null);
      setMenuConfirmed(false);
      setTitle("");
      setContent("");
      setRating(5);
      setImages([]);
    } catch (e) {
      setErr(e?.response?.data?.detail || e?.message || "리뷰 생성 실패");
    } finally {
      setLoadingCreate(false);
    }
  };

  return (
  <div className={styles.reviewCreateContainer}>
      <h2 className={styles.reviewCreateTitle}>리뷰 등록</h2>

      {/* Step 1: 영수증 인증 */}
      {!receiptId && (
        <div className={styles.stepSection}>
          <div className={styles.stepHeader}>1) 영수증 인증</div>
          <div className={styles.receiptUpload}>
            <input
              type="file"
              accept="image/*"
              onChange={(e) => setReceiptFile(e.target.files?.[0] || null)}
              className={styles.fileInput}
            />
            <button onClick={verify} disabled={loadingVerify} className={styles.btnPrimary}>
              {loadingVerify ? "⏳" : "✔"}
            </button>
          </div>
        </div>
      )}
 
      {/* Step 2: 메뉴 확인 */}
      {receiptId && extracted && (
        <div className={styles.stepSection}>
          <div className={styles.stepHeader}>2) 메뉴 확인</div>
          <div className={styles.menuConfirmSection}>
            {!menuConfirmed && <p className={styles.menuConfirmText}>다음 메뉴들이 맞나요?</p>}
            <div className={styles.menuList}>
              {extracted.menu_en && (
                Array.isArray(extracted.menu_en)
                  ? extracted.menu_en.map((menu, idx) => (
                      <div key={idx} className={styles.menuItem}>
                        <span className={styles.menuIcon}>🍽️</span>
                        <span className={styles.menuName}>{String(menu).replace(/["[\]]/g, '').trim()}</span>
                      </div>
                    ))
                  : extracted.menu_en.split(',').map((menu, idx) => (
                      <div key={idx} className={styles.menuItem}>
                        <span className={styles.menuIcon}>🍽️</span>
                        <span className={styles.menuName}>{menu.replace(/["[\]]/g, '').trim()}</span>
                      </div>
                    ))
              )}
            </div>
            {!menuConfirmed && (
              <div className={styles.menuConfirmButtons}>
                <button onClick={confirmMenu} className={styles.btnConfirm}>
                  확인
                </button>
                <button onClick={cancelMenu} className={styles.btnCancel}>
                  취소
                </button>
              </div>
            )}
          </div>
        </div>
      )}
 
      {/* Step 3: 리뷰 작성 */}
      {receiptId && menuConfirmed && (
        <div className={styles.stepSection}>
          <div className={styles.stepHeader}>3) 리뷰 작성</div>

          <div className={styles.reviewForm}>
            <div className={styles.formGroup}>
              <label className={styles.formLabel}>제목</label>
              <input
                value={title}
                onChange={(e) => setTitle(e.target.value)}
                placeholder="리뷰 제목을 입력해주세요"
                className={styles.formInput}
              />
            </div>

            <div className={styles.formGroup}>
              <label className={styles.formLabel}>내용</label>
              <textarea
                value={content}
                onChange={(e) => setContent(e.target.value)}
                placeholder="리뷰 내용을 입력해주세요"
                rows={6}
                className={styles.formTextarea}
              />
            </div>

            <div className={styles.formGroup}>
              <label className={styles.formLabel}>별점</label>
              <div className={styles.ratingSelect}>
                {[1, 2, 3, 4, 5].map((n) => (
                  <span
                    key={n}
                    onClick={() => setRating(n)}
                    className={`${styles.star} ${n <= rating ? styles.active : ''}`}
                  >
                    ★
                  </span>
                ))}
              </div>
            </div>
 
            <div className={styles.formGroup}>
              <label className={styles.formLabel}>추가 이미지 (최대 3장)</label>
              <input
                ref={imageInputRef}
                type="file"
                accept="image/*"
                multiple
                onChange={onPickImages}
                disabled={images.length >= 3}
                className={styles.fileInput}
              />
              <div className={styles.imageCount}>
                추가 이미지 {images.length}/3
              </div>

              {previewUrls.length > 0 && (
                <div className={styles.imagePreviewList}>
                  {previewUrls.map((url, idx) => (
                    <div key={idx} className={styles.imagePreviewItem}>
                      <img
                        src={url}
                        alt={`preview-${idx}`}
                        className={styles.previewImage}
                      />
                      <button
                        type="button"
                        onClick={() => removeImage(idx)}
                        className={styles.btnRemoveImage}
                        title="삭제"
                      >
                        ×
                      </button>
                    </div>
                  ))}
                </div>
              )}
            </div>

            <button onClick={create} disabled={loadingCreate} className={styles.btnSubmit}>
              {loadingCreate ? "생성중..." : "리뷰 생성"}
            </button>
          </div>
        </div>
      )}

      {msg && <div className={`${styles.message} ${styles.success}`}>{msg}</div>}
      {err && <div className={`${styles.message} ${styles.error}`}>{err}</div>}
    </div>
  );
}