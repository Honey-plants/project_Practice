import React, { useEffect, useRef, useState } from "react";
import { ReviewAPI } from "../../api/reviewApi";

export default function ReviewCreateInline({ onCreated }) {
  // Step1
  const [receiptFile, setReceiptFile] = useState(null);
  const [receiptId, setReceiptId] = useState(null);
  const [extracted, setExtracted] = useState(null);

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
      setMsg(" 영수증 인증 완료. 리뷰 정보를 입력해줘.");
    } catch (e) {
      setErr(e?.response?.data?.detail || e?.message || "영수증 인증 실패");
    } finally {
      setLoadingVerify(false);
    }
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

      setMsg(" 리뷰 생성 완료");
      onCreated?.(r.data);

      // 초기화
      setReceiptFile(null);
      setReceiptId(null);
      setExtracted(null);
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
    <div style={{ border: "1px solid #ddd", padding: 12, borderRadius: 8 }}>
      <h3 style={{ marginTop: 0 }}>리뷰 등록</h3>

      {/* Step 1 */}
      {!receiptId && (
        <div style={{ marginBottom: 12 }}>
          <div style={{ fontWeight: 700, marginBottom: 6 }}>1) 영수증 인증</div>
          <input
            type="file"
            accept="image/*"
            onChange={(e) => setReceiptFile(e.target.files?.[0] || null)}
          />
          <button onClick={verify} disabled={loadingVerify} style={{ marginLeft: 8 }}>
            {loadingVerify ? "인증중..." : "영수증 인증"}
          </button>
        </div>
      )}

      {/* Step 2 */}
      {receiptId && (
        <div>
          <div style={{ marginBottom: 10 }}>
            receipt_id: <b>{receiptId}</b>
          </div>

          {extracted && (
            <details style={{ marginBottom: 12 }}>
              <summary>OCR 추출 결과 보기</summary>
              <pre style={{ whiteSpace: "pre-wrap", background: "#fafafa", padding: 10 }}>
                {JSON.stringify(extracted, null, 2)}
              </pre>
            </details>
          )}

          <div style={{ fontWeight: 700, marginBottom: 6 }}>2) 리뷰 내용 입력</div>

          <div style={{ display: "grid", gap: 8 }}>
            <input value={title} onChange={(e) => setTitle(e.target.value)} placeholder="title" />

            <textarea
              value={content}
              onChange={(e) => setContent(e.target.value)}
              placeholder="content"
              rows={6}
            />

            <div>
              rating:&nbsp;
              <select value={rating} onChange={(e) => setRating(Number(e.target.value))}>
                {[1, 2, 3, 4, 5].map((n) => (
                  <option key={n} value={n}>
                    {n}
                  </option>
                ))}
              </select>
            </div>

            {/*  이미지 선택 */}
            <div style={{ marginTop: 6 }}>
              <div style={{ fontWeight: 700, marginBottom: 6 }}>3) 추가 이미지 (최대 3장)</div>

              <input
                ref={imageInputRef}
                type="file"
                accept="image/*"
                multiple
                onChange={onPickImages}
                disabled={images.length >= 3}
              />

              <div style={{ fontSize: 12, color: "#666", marginTop: 6 }}>
                추가 이미지 {images.length}/3
              </div>

              {/*  미리보기 + 삭제 */}
              {previewUrls.length > 0 && (
                <div style={{ display: "flex", gap: 8, marginTop: 10, flexWrap: "wrap" }}>
                  {previewUrls.map((url, idx) => (
                    <div key={idx} style={{ position: "relative" }}>
                      <img
                        src={url}
                        alt={`preview-${idx}`}
                        style={{
                          width: 110,
                          height: 110,
                          objectFit: "cover",
                          borderRadius: 8,
                          border: "1px solid #eee",
                        }}
                      />
                      <button
                        type="button"
                        onClick={() => removeImage(idx)}
                        style={{
                          position: "absolute",
                          top: -8,
                          right: -8,
                          width: 24,
                          height: 24,
                          borderRadius: "50%",
                          border: "1px solid #ccc",
                          background: "#fff",
                          cursor: "pointer",
                        }}
                        title="삭제"
                      >
                        ×
                      </button>
                    </div>
                  ))}
                </div>
              )}
            </div>

            <button onClick={create} disabled={loadingCreate}>
              {loadingCreate ? "생성중..." : "리뷰 생성"}
            </button>
          </div>
        </div>
      )}

      {msg && <div style={{ marginTop: 10 }}>{msg}</div>}
      {err && <div style={{ marginTop: 10, color: "crimson" }}>{err}</div>}
    </div>
  );
}
