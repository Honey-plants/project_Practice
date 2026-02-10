import React, { useEffect, useRef, useState } from "react";
import { ReviewAPI } from "../../api/reviewApi";
import { useNavigate } from "react-router-dom";
import styles from "./ReviewCreate.module.css";

export default function ReviewCreateInline({ onCreated }) {
  const navigate = useNavigate();
  // Step1
  const [receiptFile, setReceiptFile] = useState(null);
  const [receiptPreviewUrl, setReceiptPreviewUrl] = useState(null);
  const [receiptId, setReceiptId] = useState(null);
  const [extracted, setExtracted] = useState(null);
  const [menuList, setMenuList] = useState([]);
  const [menuConfirmed, setMenuConfirmed] = useState(false);

  // Step2
  const [title, setTitle] = useState("");
  const [content, setContent] = useState("");
  const [rating, setRating] = useState(5);

  //  images: File[]
  const [images, setImages] = useState([]);
  //  preview urls
  const [previewUrls, setPreviewUrls] = useState([]);

  const receiptInputRef = useRef(null);
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
    if (!receiptFile) return setErr("영수증 이미지를 선택해줘");

    setLoadingVerify(true);
    try {
      const r = await ReviewAPI.verifyReceipt(receiptFile);
      const ext = r.data?.extracted || null;

      // location(coords) 검증: 상호 주소가 없으면 재선택 유도
      const coords = ext?.coords;
      if (!coords || coords.x == null || coords.y == null) {
        alert("Please attach the receipt with the store address again");
        // 이미지 선택 초기화
        setReceiptFile(null);
        if (receiptPreviewUrl) URL.revokeObjectURL(receiptPreviewUrl);
        setReceiptPreviewUrl(null);
        setReceiptId(null);
        setExtracted(null);
        setMenuList([]);
        // 같은 파일 다시 선택 가능하도록 input reset
        if (receiptInputRef.current) receiptInputRef.current.value = "";
        setLoadingVerify(false);
        return;
      }

      setReceiptId(r.data?.receipt_id);
      setExtracted(ext);
      // OCR 결과에서 메뉴 목록 파싱하여 state에 저장
      if (ext?.menu_en) {
        const raw = ext.menu_en;
        const parsed = Array.isArray(raw)
          ? raw.map((m) => String(m).replace(/["[\]]/g, '').trim())
          : raw.split(',').map((m) => m.replace(/["[\]]/g, '').trim());
        setMenuList(parsed.filter(Boolean));
      }
      setMsg("Receipt certified. Please check the menu.");
    } catch (e) {
      setErr(e?.response?.data?.detail || e?.message || "Receipt authentication failed");
    } finally {
      setLoadingVerify(false);
    }
  };

  const confirmMenu = () => {
    setMenuConfirmed(true);
    setMsg("Checked the menu. Please write a review.");
  };

  const cancelMenu = () => {
    setReceiptId(null);
    setExtracted(null);
    setMenuList([]);
    setReceiptFile(null);
    if (receiptPreviewUrl) URL.revokeObjectURL(receiptPreviewUrl);
    setReceiptPreviewUrl(null);
    setMenuConfirmed(false);
    setMsg("");
    setErr("");
    // 같은 파일 다시 선택 가능하도록 input reset
    if (receiptInputRef.current) receiptInputRef.current.value = "";
  };

  const removeMenu = (idx) => {
    setMenuList((prev) => prev.filter((_, i) => i !== idx));
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
        setErr("Upload up to three images.");
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

    if (!receiptId) return setErr("Please verify the receipt first");
    if (!title.trim()) return setErr("Please enter the title");
    if (!content.trim()) return setErr("Please enter the content");
    if (images.length > 3) return setErr("upload up to three images.");

    setLoadingCreate(true);
    try {
      const r = await ReviewAPI.createFromReceipt({
        receipt_id: receiptId,
        title,
        content,
        rating,
        menu_name: JSON.stringify(menuList),
        images, //  File[] 그대로
      });

      setMsg("Completion of review creation");

      // 리뷰 페이지로 이동 (내 리뷰만 필터 활성화)
      navigate("/review?mine=true");

      onCreated?.(r.data);

      // 초기화
      setReceiptFile(null);
      if (receiptPreviewUrl) URL.revokeObjectURL(receiptPreviewUrl);
      setReceiptPreviewUrl(null);
      setReceiptId(null);
      setExtracted(null);
      setMenuList([]);
      setMenuConfirmed(false);
      setTitle("");
      setContent("");
      setRating(5);
      setImages([]);
    } catch (e) {
      setErr(e?.response?.data?.detail || e?.message || "Failed to create review");
    } finally {
      setLoadingCreate(false);
    }
  };

  return (
  <div className={styles.reviewCreateContainer}>
      {loadingVerify && (
        <div className={styles.loadingOverlay}>
          <div className={styles.loadingBox}>
            <div className={styles.loadingSpinner} />
            <p className={styles.loadingText}>Detecting Receipt...</p>
          </div>
        </div>
      )}
      <h2 className={styles.reviewCreateTitle}>Create Review</h2>

      {/* Step 1: 영수증 인증 */}
      {!receiptId && (
        <div className={styles.stepSection}>
          <div className={styles.stepHeader}>1) Verify Receipt</div>
          <div className={styles.receiptUpload}>
            <input
              ref={receiptInputRef}
              type="file"
              accept="image/*"
              disabled={loadingVerify}
              onChange={(e) => {
                const f = e.target.files?.[0] || null;
                setReceiptFile(f);
                if (receiptPreviewUrl) URL.revokeObjectURL(receiptPreviewUrl);
                setReceiptPreviewUrl(f ? URL.createObjectURL(f) : null);
              }}
              className={styles.fileInput}
            />
            <button onClick={verify} disabled={loadingVerify} className={styles.btnPrimary}>
              {loadingVerify ? "⏳" : "✔"}
            </button>
          </div>
          {receiptPreviewUrl && (
            <div className={styles.receiptPreview}>
              <img
                src={receiptPreviewUrl}
                alt="Preview Receipts"
                className={styles.receiptPreviewImage}
              />
            </div>
          )}
        </div>
      )}
 
      {/* Step 2: 메뉴 확인 */}
      {receiptId && extracted && (
        <div className={styles.stepSection}>
          <div className={styles.stepHeader}>2) Confirm Receipt Details</div>
          <p>{extracted.store_name} / {extracted.store_name_en}</p>
          <div className={styles.menuConfirmSection}>
            {!menuConfirmed && <p className={styles.menuConfirmText}>Please only select your menu</p>}
            <div className={styles.menuList}>
              {menuList.length > 0
                ? menuList.map((menu, idx) => (
                    <div key={idx} className={styles.menuItem}>
                      <span className={styles.menuIcon}>🍽️</span>
                      <span className={styles.menuName}>{menu}</span>
                      {!menuConfirmed && (
                        <button
                          type="button"
                          onClick={() => removeMenu(idx)}
                          className={styles.btnRemoveMenu}
                          title="Delete Menu"
                        >
                          ×
                        </button>
                      )}
                    </div>
                  ))
                : <p className={styles.menuConfirmText}>There's no menu.</p>
              }
            </div>
            {!menuConfirmed && (
              <div className={styles.menuConfirmButtons}>
                <button onClick={confirmMenu} disabled={menuList.length === 0} className={styles.btnConfirm}>
                  Confirm
                </button>
                <button onClick={cancelMenu} className={styles.btnCancel}>
                  Cancel
                </button>
              </div>
            )}
          </div>
        </div>
      )}
 
      {/* Step 3: 리뷰 작성 */}
      {receiptId && menuConfirmed && (
        <div className={styles.stepSection}>
          <div className={styles.stepHeader}>3) Review Details</div>

          <div className={styles.reviewForm}>
            <div className={styles.formGroup}>
              <label className={styles.formLabel}>Title</label>
              <input
                value={title}
                onChange={(e) => setTitle(e.target.value)}
                placeholder="Enter review title"
                className={styles.formInput}
              />
            </div>

            <div className={styles.formGroup}>
              <label className={styles.formLabel}>Content</label>
              <textarea
                value={content}
                onChange={(e) => setContent(e.target.value)}
                placeholder="Enter review content"
                rows={6}
                className={styles.formTextarea}
              />
            </div>

            <div className={styles.formGroup}>
              <label className={styles.formLabel}>Rating</label>
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
              <label className={styles.formLabel}>추가 이미지 (max 3)</label>
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
                Additional Images {images.length}/3
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
                        title="Delete"
                      >
                        ×
                      </button>
                    </div>
                  ))}
                </div>
              )}
            </div>

            <button onClick={create} disabled={loadingCreate} className={styles.btnSubmit}>
              {loadingCreate ? "Creating..." : "Save"}
            </button>
          </div>
        </div>
      )}

      {msg && <div className={`${styles.message} ${styles.success}`}>{msg}</div>}
      {err && <div className={`${styles.message} ${styles.error}`}>{err}</div>}
    </div>
  );
}