import React, { useState } from "react";
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
  const [images, setImages] = useState([]);

  const [loadingVerify, setLoadingVerify] = useState(false);
  const [loadingCreate, setLoadingCreate] = useState(false);
  const [msg, setMsg] = useState("");
  const [err, setErr] = useState("");

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
        images,
      });

      setMsg(" 리뷰 생성 완료");
      onCreated?.(r.data); // 부모에서 list reload 같은거 가능

      // 초기화(원하면 유지해도 됨)
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
                  <option key={n} value={n}>{n}</option>
                ))}
              </select>
            </div>

            <input
              type="file"
              accept="image/*"
              multiple
              onChange={(e) => setImages(Array.from(e.target.files || []).slice(0, 3))}
            />
            <div style={{ fontSize: 12, color: "#666" }}>추가 이미지 {images.length}/3</div>

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