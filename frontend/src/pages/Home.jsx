import MenuUpload from "../components/menu/MenuUpload";
import React, { useState, useRef } from "react";
import { MenuAPI } from "../api/menuApi";
import ResultPage from "./menuscan/ResultPage";
import "./Home.css";

export default function Home() {
  const [selectedImage, setSelectedImage] = useState(null);
  const [imagePreview, setImagePreview] = useState(null);
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState("");
  const fileInputRef = useRef(null);

  const handleImageSelect = (e) => {
    const file = e.target.files?.[0];
    if (file) {
      setSelectedImage(file);
      setImagePreview(URL.createObjectURL(file));
      setMessage("");
    }
  };

  const handleCameraClick = () => {
    // 카메라 기능은 모바일에서 input[type=file] capture 속성 사용
    if (fileInputRef.current) {
      fileInputRef.current.setAttribute("capture", "environment");
      fileInputRef.current.click();
    }
  };

  const handleFileSelectClick = () => {
    if (fileInputRef.current) {
      fileInputRef.current.removeAttribute("capture");
      fileInputRef.current.click();
    }
  };

  const handleAnalyze = async () => {
    if (!selectedImage) {
      setMessage("이미지를 먼저 선택해주세요.");
      return;
    }

    setLoading(true);
    setMessage("");

    try {
      const response = await MenuAPI.uploadMenu(selectedImage);
      setResult(response);
      setMessage("분석 완료!");
    } catch (error) {
      setMessage(`분석 실패: ${error?.response?.data?.detail || error?.message || "알 수 없는 오류"}`);
    } finally {
      setLoading(false);
    }
  };

  const handleReset = () => {
    setSelectedImage(null);
    setImagePreview(null);
    setResult(null);
    setMessage("");
    if (fileInputRef.current) {
      fileInputRef.current.value = "";
    }
  };

  if (result) {
    return (
      <div className="home-result-container">
        <button
          onClick={handleReset}
          className="home-button-reset"
        >
          다시 분석하기
        </button>
        <ResultPage result={result?.data ?? result} />
      </div>
    );
  }

  return (
    <div className="home-container">
      <div className="home-title">
        <p>
          Please take a picture or choose an image
        </p>
      </div>

      <input
        ref={fileInputRef}
        type="file"
        accept="image/*"
        onChange={handleImageSelect}
        style={{ display: "none" }}
      />

      {imagePreview && (
        <div className="home-image-preview">
          <img
            src={imagePreview}
            alt="선택된 이미지"
          />
        </div>
      )}

      <div className="home-button-container">
        <button
          onClick={handleCameraClick}
          className="home-button home-button-camera"
        >
          사진 찍기
        </button>

        <button
          onClick={handleFileSelectClick}
          className="home-button home-button-file"
        >
          이미지 선택하기
        </button>

        <button
          onClick={handleAnalyze}
          disabled={loading || !selectedImage}
          className="home-button home-button-analyze"
        >
          {loading ? "분석 중..." : "이미지 분석"}
        </button>
      </div>

      {message && (
        <div className={`home-message ${message.includes("실패") ? "home-message-error" : "home-message-success"}`}>
          {message}
        </div>
      )}
    </div>
  );
}
