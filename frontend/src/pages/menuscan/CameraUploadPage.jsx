import React, { useState } from "react";
import PreviewPage from "./PreviewPage";

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
    <div className="camera-upload-page">
      {!previewStep ? (
        <>
          <h2>Menu Scan</h2>

          {/* 카메라 / 파일 공용 */}
          <input
            type="file"
            accept="image/*"
            capture="environment"
            onChange={handleFileChange}
          />

          <p>Take a photo or select an image.</p>
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
