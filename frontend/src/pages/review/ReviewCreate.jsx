import React, { useEffect, useRef, useState } from "react";
import { ReviewAPI } from "../../api/reviewApi";
import { useNavigate } from "react-router-dom";
import "./ReviewCreate.css";

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
    if (!receiptFile) return setErr("영수증 이미지를 선택해줘");

    setLoadingVerify(true);
    try {
      const r = await ReviewAPI.verifyReceipt(receiptFile);
      setReceiptId(r.data?.receipt_id);
      setExtracted(r.data?.extracted || null);
      setMsg("영수증 인증 완료. 메뉴를 확인해주세요.");
    } catch (e) {
      setErr(e?.response?.data?.detail || e?.message || "영수증 인증 실패");
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
  <div className="review-create-container">
      <h2 className="review-create-title">리뷰 등록</h2>
 
      {/* Step 1: 영수증 인증 */}
      {!receiptId && (
        <div className="step-section">
          <div className="step-header">1) 영수증 인증</div>
          <div className="receipt-upload">
            <input
              type="file"
              accept="image/*"
              onChange={(e) => setReceiptFile(e.target.files?.[0] || null)}
              className="file-input"
            />
            <button onClick={verify} disabled={loadingVerify} className="btn-primary">
              {loadingVerify ? "인증중..." : "영수증 인증"}
            </button>
          </div>
        </div>
      )}
 
      {/* Step 2: 메뉴 확인 */}
      {receiptId && extracted && (
        <div className="step-section">
          <div className="step-header">2) 메뉴 확인</div>
          <div className="menu-confirm-section">
            {!menuConfirmed && <p className="menu-confirm-text">다음 메뉴들이 맞나요?</p>}
            <div className="menu-list">
              {extracted.menu_name && (
                Array.isArray(extracted.menu_name)
                  ? extracted.menu_name.map((menu, idx) => (
                      <div key={idx} className="menu-item">
                        <span className="menu-icon">🍽️</span>
                        <span className="menu-name">{String(menu).replace(/["[\]]/g, '').trim()}</span>
                      </div>
                    ))
                  : extracted.menu_name.split(',').map((menu, idx) => (
                      <div key={idx} className="menu-item">
                        <span className="menu-icon">🍽️</span>
                        <span className="menu-name">{menu.replace(/["[\]]/g, '').trim()}</span>
                      </div>
                    ))
              )}
            </div>
            {!menuConfirmed && (
              <div className="menu-confirm-buttons">
                <button onClick={confirmMenu} className="btn-confirm">
                  확인
                </button>
                <button onClick={cancelMenu} className="btn-cancel">
                  취소
                </button>
              </div>
            )}
          </div>
        </div>
      )}
 
      {/* Step 3: 리뷰 작성 */}
      {receiptId && menuConfirmed && (
        <div className="step-section">
          <div className="step-header">3) 리뷰 작성</div>
 
          <div className="review-form">
            <div className="form-group">
              <label className="form-label">제목</label>
              <input
                value={title}
                onChange={(e) => setTitle(e.target.value)}
                placeholder="리뷰 제목을 입력해주세요"
                className="form-input"
              />
            </div>
 
            <div className="form-group">
              <label className="form-label">내용</label>
              <textarea
                value={content}
                onChange={(e) => setContent(e.target.value)}
                placeholder="리뷰 내용을 입력해주세요"
                rows={6}
                className="form-textarea"
              />
            </div>
 
            <div className="form-group">
              <label className="form-label">별점</label>
              <div className="rating-select">
                {[1, 2, 3, 4, 5].map((n) => (
                  <span
                    key={n}
                    onClick={() => setRating(n)}
                    className={`star ${n <= rating ? 'active' : ''}`}
                  >
                    ★
                  </span>
                ))}
              </div>
            </div>
 
            <div className="form-group">
              <label className="form-label">추가 이미지 (최대 3장)</label>
              <input
                ref={imageInputRef}
                type="file"
                accept="image/*"
                multiple
                onChange={onPickImages}
                disabled={images.length >= 3}
                className="file-input"
              />
              <div className="image-count">
                추가 이미지 {images.length}/3
              </div>
 
              {previewUrls.length > 0 && (
                <div className="image-preview-list">
                  {previewUrls.map((url, idx) => (
                    <div key={idx} className="image-preview-item">
                      <img
                        src={url}
                        alt={`preview-${idx}`}
                        className="preview-image"
                      />
                      <button
                        type="button"
                        onClick={() => removeImage(idx)}
                        className="btn-remove-image"
                        title="삭제"
                      >
                        ×
                      </button>
                    </div>
                  ))}
                </div>
              )}
            </div>
 
            <button onClick={create} disabled={loadingCreate} className="btn-submit">
              {loadingCreate ? "생성중..." : "리뷰 생성"}
            </button>
          </div>
        </div>
      )}
 
      {msg && <div className="message success">{msg}</div>}
      {err && <div className="message error">{err}</div>}
    </div>
  );
}