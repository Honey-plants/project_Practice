import React, { useState } from "react";
import PreviewPage from "./PreviewPage";
import "./CameraUploadPage.css";

export default function CameraUploadPage() {
  const [file, setFile] = useState(null);
  const [previewStep, setPreviewStep] = useState(false);

  const handleFileChange = (e) => {
    const f = e.target.files?.[0];
    if (!f) return;
    setFile(f);
    setPreviewStep(true);
  };

  return (
    <div className="ms-cup__root">
      {!previewStep ? (
        <>
          <h2 className="ms-cup__title">Menu Scan</h2>

          {/* 카메라 / 파일 공용 */}
          <input
            className="ms-cup__input"
            type="file"
            accept="image/*"
            capture="environment"
            onChange={handleFileChange}
          />

          <p className="ms-cup__hint">Take a photo or select an image.</p>
        </>
      ) : (
        <PreviewPage
          file={file}
          goBack={() => {
            setFile(null);
            setPreviewStep(false);
          }}
        />
      )}
    </div>
  );
}
