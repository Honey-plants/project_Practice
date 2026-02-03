import React, { useState } from "react";
import { menuUploadAPI } from "../../api/menuUploadApi";
import ResultPage from "./ResultPage";

export default function PreviewPage({ file, goBack }) {
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState("");
  const [result, setResult] = useState(null);

  const handleUpload = async () => {
    if (!file) return;

    const formData = new FormData();
    formData.append("image", file); // FastAPI expects "image"
    formData.append("type", "menu");

    setUploading(true);
    setError("");

    try {
      const res = await menuUploadAPI.upload(formData);

      /**
       * AI 연동 전/후 공통
       * - res.data가 placeholder여도 OK
       * - AI 최종 JSON 그대로 ResultPage로 전달
       */
      setResult(res.data);
    } catch (e) {
      console.error(e);
      setError("Upload failed");
    } finally {
      setUploading(false);
    }
  };

  if (result) {
    return <ResultPage result={result} />;
  }

  return (
    <div className="preview-page">
      <img
        src={URL.createObjectURL(file)}
        alt="preview"
        style={{ maxWidth: "100%" }}
      />

      <div style={{ marginTop: 16 }}>
        <button onClick={goBack}>Retake</button>
        <button onClick={handleUpload} disabled={uploading}>
          {uploading ? "Uploading..." : "Send to AI"}
        </button>
      </div>

      {error && <p style={{ color: "red" }}>{error}</p>}
    </div>
  );
}