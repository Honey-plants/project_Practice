import React, { useState, useRef, useEffect } from "react";
import { ReviewAPI } from "../../api/reviewApi";

export default function ReviewCreateForm({ onCreated }) {
  // Step 1: 영수증 인증
  const [receiptFile, setReceiptFile] = useState(null);
  const [receiptId, setReceiptId] = useState(null);
  const [extracted, setExtracted] = useState(null);
  const [menuConfirmed, setMenuConfirmed] = useState(false);

  // Step 2: 리뷰 작성
  const [title, setTitle] = useState("");
  const [content, setContent] = useState("");
  const [rating, setRating] = useState(5);
  const [images, setImages] = useState([]);
  const [previewUrls, setPreviewUrls] = useState([]);

  const imageInputRef = useRef(null);

  const [loadingVerify, setLoadingVerify] = useState(false);
  const [loadingCreate, setLoadingCreate] = useState(false);
  const [msg, setMsg] = useState("");
  const [err, setErr] = useState("");

  // 이미지 미리보기 URL 생성 및 정리
  useEffect(() => {
    previewUrls.forEach((url) => URL.revokeObjectURL(url));
    const newUrls = images.map((file) => URL.createObjectURL(file));
    setPreviewUrls(newUrls);

    return () => {
      newUrls.forEach((url) => URL.revokeObjectURL(url));
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [images]);

  // 영수증 인증
  const verify = async () => {
    setErr("");
    setMsg("");
    if (!receiptFile) return setErr("영수증 이미지를 선택해주세요");

    setLoadingVerify(true);
    try {
      const r = await ReviewAPI.verifyReceipt(receiptFile);
      setReceiptId(r.data?.receipt_id);
      setExtracted(r.data?.extracted || null);

      // OCR 결과로 메뉴 이름 추출
      const menuName = r.data?.extracted?.menu_name || "확인되지 않은 메뉴";

      // confirm 창으로 메뉴 이름 확인
      const isConfirmed = window.confirm(
        `번역된 메뉴 이름: "${menuName}"\n\n이 메뉴 이름이 맞습니까?`
      );

      if (isConfirmed) {
        setMenuConfirmed(true);
        setMsg("✅ 영수증 인증 완료! 리뷰를 작성해주세요.");
      } else {
        // 거부시 다시 선택하도록
        setReceiptId(null);
        setExtracted(null);
        setReceiptFile(null);
        setErr("메뉴 이름이 맞지 않습니다. 다시 영수증을 업로드해주세요.");
      }
    } catch (e) {
      setErr(e?.response?.data?.detail || e?.message || "영수증 인증 실패");
    } finally {
      setLoadingVerify(false);
    }
  };

  // 이미지 추가 (최대 3장)
  const onPickImages = (e) => {
    const files = Array.from(e.target.files || []);
    if (!files.length) return;

    setErr("");
    setMsg("");

    setImages((prev) => {
      const merged = [...prev, ...files];
      if (merged.length > 3) {
        setErr("이미지는 최대 3장까지 업로드 가능합니다.");
        return prev;
      }
      return merged;
    });

    // input 초기화 (같은 파일 재선택 가능)
    if (imageInputRef.current) imageInputRef.current.value = "";
  };

  // 개별 이미지 삭제
  const removeImage = (idx) => {
    setImages((prev) => prev.filter((_, i) => i !== idx));
  };

  // 리뷰 생성
  const create = async () => {
    setErr("");
    setMsg("");

    if (!receiptId) return setErr("먼저 영수증 인증을 해주세요");
    if (!menuConfirmed) return setErr("메뉴 이름을 확인해주세요");
    if (!title.trim()) return setErr("리뷰 제목을 입력해주세요");
    if (!content.trim()) return setErr("리뷰 내용을 입력해주세요");
    if (images.length > 3) return setErr("이미지는 최대 3장까지 가능합니다");

    setLoadingCreate(true);
    try {
      const r = await ReviewAPI.createFromReceipt({
        receipt_id: receiptId,
        title,
        content,
        rating,
        images,
      });

      setMsg("✅ 리뷰가 성공적으로 등록되었습니다!");

      // 부모 컴포넌트에 알림
      if (onCreated) onCreated(r.data);

      // 폼 초기화
      setTimeout(() => {
        setReceiptFile(null);
        setReceiptId(null);
        setExtracted(null);
        setMenuConfirmed(false);
        setTitle("");
        setContent("");
        setRating(5);
        setImages([]);
      }, 1000);
    } catch (e) {
      setErr(e?.response?.data?.detail || e?.message || "리뷰 생성 실패");
    } finally {
      setLoadingCreate(false);
    }
  };

  return (
    <div style={{
      maxWidth: "800px",
      margin: "0 auto",
      padding: "32px",
      background: "white",
      borderRadius: "16px",
      boxShadow: "0 4px 12px rgba(0,0,0,0.1)"
    }}>
      <h2 style={{ marginTop: 0, marginBottom: "24px", fontSize: "24px", fontWeight: "700" }}>
        리뷰 작성
      </h2>

      {/* Step 1: 영수증 인증 */}
      {!receiptId && (
        <div style={{
          padding: "24px",
          background: "#f8f9fa",
          borderRadius: "12px",
          marginBottom: "20px"
        }}>
          <h3 style={{
            marginTop: 0,
            marginBottom: "16px",
            fontSize: "18px",
            fontWeight: "600",
            color: "#495057"
          }}>
            1️⃣ 영수증 인증
          </h3>

          <input
            type="file"
            accept="image/*"
            onChange={(e) => setReceiptFile(e.target.files?.[0] || null)}
            style={{
              display: "block",
              marginBottom: "12px",
              padding: "8px",
              width: "100%",
              border: "1px solid #ced4da",
              borderRadius: "6px"
            }}
          />

          <button
            onClick={verify}
            disabled={loadingVerify || !receiptFile}
            style={{
              padding: "12px 24px",
              background: loadingVerify || !receiptFile ? "#ccc" : "#007bff",
              color: "white",
              border: "none",
              borderRadius: "6px",
              cursor: loadingVerify || !receiptFile ? "not-allowed" : "pointer",
              fontWeight: "600",
              fontSize: "14px"
            }}
          >
            {loadingVerify ? "인증중..." : "영수증 인증하기"}
          </button>
        </div>
      )}

      {/* Step 2: 리뷰 작성 (영수증 인증 & 메뉴 확인 완료 후) */}
      {receiptId && menuConfirmed && (
        <div style={{ marginTop: "24px" }}>
          <div style={{
            padding: "12px 16px",
            background: "#d1ecf1",
            borderRadius: "8px",
            marginBottom: "20px",
            fontSize: "14px",
            color: "#0c5460",
            border: "1px solid #bee5eb"
          }}>
            ✅ 영수증 인증 완료 (Receipt ID: <strong>{receiptId}</strong>)
          </div>

          {/* OCR 결과 표시 (선택사항) */}
          {extracted && (
            <details style={{ marginBottom: "20px" }}>
              <summary style={{
                cursor: "pointer",
                fontWeight: "600",
                color: "#495057",
                padding: "8px 0"
              }}>
                📄 OCR 추출 결과 보기
              </summary>
              <pre style={{
                whiteSpace: "pre-wrap",
                background: "#f8f9fa",
                padding: "16px",
                borderRadius: "8px",
                fontSize: "12px",
                overflow: "auto",
                marginTop: "8px"
              }}>
                {JSON.stringify(extracted, null, 2)}
              </pre>
            </details>
          )}

          <h3 style={{
            marginBottom: "16px",
            fontSize: "18px",
            fontWeight: "600",
            color: "#495057"
          }}>
            2️⃣ 리뷰 내용 입력
          </h3>

          {/* 제목 */}
          <div style={{ marginBottom: "16px" }}>
            <label style={{
              display: "block",
              marginBottom: "8px",
              fontWeight: "600",
              fontSize: "14px",
              color: "#495057"
            }}>
              리뷰 제목 *
            </label>
            <input
              type="text"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              placeholder="예: 맛있었던 점심 식사"
              style={{
                width: "100%",
                padding: "12px",
                border: "1px solid #ced4da",
                borderRadius: "6px",
                fontSize: "14px",
                boxSizing: "border-box"
              }}
            />
          </div>

          {/* 내용 */}
          <div style={{ marginBottom: "16px" }}>
            <label style={{
              display: "block",
              marginBottom: "8px",
              fontWeight: "600",
              fontSize: "14px",
              color: "#495057"
            }}>
              리뷰 내용 *
            </label>
            <textarea
              value={content}
              onChange={(e) => setContent(e.target.value)}
              placeholder="음식의 맛, 서비스, 분위기 등을 자유롭게 작성해주세요"
              rows={6}
              style={{
                width: "100%",
                padding: "12px",
                border: "1px solid #ced4da",
                borderRadius: "6px",
                fontSize: "14px",
                resize: "vertical",
                boxSizing: "border-box"
              }}
            />
          </div>

          {/* 평점 */}
          <div style={{ marginBottom: "20px" }}>
            <label style={{
              display: "block",
              marginBottom: "8px",
              fontWeight: "600",
              fontSize: "14px",
              color: "#495057"
            }}>
              평점 *
            </label>
            <div style={{ display: "flex", gap: "8px", alignItems: "center" }}>
              {[1, 2, 3, 4, 5].map((n) => (
                <button
                  key={n}
                  type="button"
                  onClick={() => setRating(n)}
                  style={{
                    fontSize: "32px",
                    background: "none",
                    border: "none",
                    cursor: "pointer",
                    color: n <= rating ? "#ffc107" : "#ddd",
                    transition: "color 0.2s"
                  }}
                >
                  ★
                </button>
              ))}
              <span style={{ marginLeft: "12px", fontSize: "18px", fontWeight: "600", color: "#495057" }}>
                {rating}점
              </span>
            </div>
          </div>

          {/* 이미지 업로드 */}
          <div style={{ marginBottom: "24px" }}>
            <label style={{
              display: "block",
              marginBottom: "8px",
              fontWeight: "600",
              fontSize: "14px",
              color: "#495057"
            }}>
              이미지 (최소 0장, 최대 3장)
            </label>

            <input
              ref={imageInputRef}
              type="file"
              accept="image/*"
              multiple
              onChange={onPickImages}
              disabled={images.length >= 3}
              style={{
                display: "block",
                marginBottom: "8px",
                padding: "8px",
                border: "1px solid #ced4da",
                borderRadius: "6px",
                width: "100%",
                boxSizing: "border-box"
              }}
            />

            <div style={{
              fontSize: "13px",
              color: "#6c757d",
              marginBottom: "12px"
            }}>
              {images.length}/3장 업로드됨
            </div>

            {/* 이미지 미리보기 */}
            {previewUrls.length > 0 && (
              <div style={{
                display: "flex",
                gap: "12px",
                flexWrap: "wrap"
              }}>
                {previewUrls.map((url, idx) => (
                  <div
                    key={idx}
                    style={{
                      position: "relative",
                      width: "120px",
                      height: "120px"
                    }}
                  >
                    <img
                      src={url}
                      alt={`preview-${idx}`}
                      style={{
                        width: "100%",
                        height: "100%",
                        objectFit: "cover",
                        borderRadius: "8px",
                        border: "2px solid #e0e0e0"
                      }}
                    />
                    <button
                      type="button"
                      onClick={() => removeImage(idx)}
                      style={{
                        position: "absolute",
                        top: "-8px",
                        right: "-8px",
                        width: "28px",
                        height: "28px",
                        borderRadius: "50%",
                        background: "#dc3545",
                        color: "white",
                        border: "2px solid white",
                        cursor: "pointer",
                        fontSize: "18px",
                        fontWeight: "bold",
                        display: "flex",
                        alignItems: "center",
                        justifyContent: "center",
                        lineHeight: "1",
                        boxShadow: "0 2px 6px rgba(0,0,0,0.2)"
                      }}
                      title="이미지 삭제"
                    >
                      ×
                    </button>
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* 등록 버튼 */}
          <button
            onClick={create}
            disabled={loadingCreate}
            style={{
              width: "100%",
              padding: "16px",
              background: loadingCreate ? "#ccc" : "#28a745",
              color: "white",
              border: "none",
              borderRadius: "8px",
              fontSize: "16px",
              fontWeight: "700",
              cursor: loadingCreate ? "not-allowed" : "pointer",
              transition: "background 0.2s"
            }}
            onMouseEnter={(e) => {
              if (!loadingCreate) e.currentTarget.style.background = "#218838";
            }}
            onMouseLeave={(e) => {
              if (!loadingCreate) e.currentTarget.style.background = "#28a745";
            }}
          >
            {loadingCreate ? "등록 중..." : "리뷰 등록하기"}
          </button>
        </div>
      )}

      {/* 메시지 표시 */}
      {msg && (
        <div style={{
          marginTop: "16px",
          padding: "12px 16px",
          background: "#d4edda",
          color: "#155724",
          borderRadius: "8px",
          border: "1px solid #c3e6cb",
          fontSize: "14px"
        }}>
          {msg}
        </div>
      )}

      {err && (
        <div style={{
          marginTop: "16px",
          padding: "12px 16px",
          background: "#f8d7da",
          color: "#721c24",
          borderRadius: "8px",
          border: "1px solid #f5c6cb",
          fontSize: "14px"
        }}>
          {err}
        </div>
      )}
    </div>
  );
}
