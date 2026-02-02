import React, { useState } from "react";
import { menuUploadAPI } from "../../api/menuUploadApi";
import ResultPage from "./ResultPage";
import { useNavigate } from "react-router-dom";
export default function PreviewPage({ file, goBack }) {
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState("");
  const [result, setResult] = useState(null);
  const navigate = useNavigate();
  const handleUpload = async () => {
    if (!file) return;

    const formData = new FormData();
    // ✅ FastAPI router는 보통 UploadFile 이름이 "file"
    formData.append("file", file);
    // ✅ 혹시 기존 구현이 "image"였을 수도 있으니 호환용으로 같이 보냄
    formData.append("image", file);
    formData.append("type", "menu");

    setUploading(true);
    setError("");

    try {
      const res = await menuUploadAPI.upload(formData);
      setResult(res.data);
      navigate("/upload/result", { state: { result: res.data } });
    } catch (e) {
      console.error(e);
      setError(e?.response?.data?.detail || "Upload failed");
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
        style={{ maxWidth: "100%", display: "block" }}
      />

      <div style={{ marginTop: 16, display: "flex", gap: 8 }}>
        <button onClick={goBack}>Retake</button>
        <button onClick={handleUpload} disabled={uploading}>
          {uploading ? "Uploading..." : "Send to AI"}
        </button>
      </div>

      {error && <p style={{ color: "red" }}>{error}</p>}
    </div>
  );
}
