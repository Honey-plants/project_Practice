import React, { useState, useRef } from "react";
import { useNavigate } from "react-router-dom";
import CameraCapture from "../components/camera/CameraCapture";
import "./Home.css";

const LOGO_SRC = "/food_ray_logo.png";

/* ── SVG 아이콘 ── */
const CameraIcon = () => (
  <svg width="26" height="26" viewBox="0 0 24 24" fill="none">
    <path
      d="M23 19a2 2 0 0 1-2 2H3a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h4l2-3h6l2 3h4a2 2 0 0 1 2 2z"
      stroke="currentColor"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
    />
    <circle
      cx="12"
      cy="13"
      r="4"
      stroke="currentColor"
      strokeWidth="2"
    />
  </svg>
);

const ImageIcon = () => (
  <svg width="26" height="26" viewBox="0 0 24 24" fill="none">
    <rect
      x="3"
      y="3"
      width="18"
      height="18"
      rx="2"
      ry="2"
      stroke="currentColor"
      strokeWidth="2"
    />
    <circle cx="8.5" cy="8.5" r="1.5" stroke="currentColor" strokeWidth="2" />
    <polyline
      points="21,15 16,10 5,21"
      stroke="currentColor"
      strokeWidth="2"
    />
  </svg>
);

const AnalyzeIcon = () => (
  <svg width="28" height="28" viewBox="0 0 24 24" fill="none">
    <circle cx="11" cy="11" r="8" stroke="currentColor" strokeWidth="2.2" />
    <line x1="21" y1="21" x2="16.65" y2="16.65" stroke="currentColor" strokeWidth="2.2" />
  </svg>
);

export default function Home() {
  const navigate = useNavigate();
  const fileInputRef = useRef(null);

  const [selectedImage, setSelectedImage] = useState(null);
  const [logoSrc, setLogoSrc] = useState(LOGO_SRC);
  const [cameraVisible, setCameraVisible] = useState(false);

  /* ===== 이미지 파일 선택 ===== */
  const handleImageSelect = (e) => {
    const file = e.target.files?.[0];
    if (!file) return;
    setSelectedImage(file);
    setLogoSrc(URL.createObjectURL(file));
  };

  const handleFileSelectClick = () => {
    if (!fileInputRef.current) return;
    fileInputRef.current.removeAttribute("capture");
    fileInputRef.current.click();
  };

  /* ===== 카메라 ===== */
  const handleCameraClick = () => {
    setCameraVisible(true); // user gesture
  };

  const handleCaptureComplete = (file) => {
    setCameraVisible(false);
    setSelectedImage(file);
    setLogoSrc(URL.createObjectURL(file));
  };

  /* ===== 분석 ===== */
  const handleAnalyze = () => {
    if (!selectedImage) return;
    window.__menuFile = selectedImage;
    navigate("/result");
  };

  return (
    <div className="home-container">
      {/* ===== 로고 + 카메라 영역 ===== */}
      <div className="home-logo-wrap">
        {/* 카메라 레이어 */}
        <div className="home-camera-layer">
          {cameraVisible && (
            <CameraCapture onComplete={handleCaptureComplete} />
          )}
        </div>

        {/* 흰 커버 */}
        <div className={`home-white-cover ${cameraVisible ? "hide" : ""}`} />

        {/* 로고 / 미리보기 */}
        <img
          src={logoSrc}
          alt="logo"
          className={`home-logo-overlay ${cameraVisible ? "hide" : ""}`}
        />
      </div>

      {/* 숨김 파일 input */}
      <input
        ref={fileInputRef}
        type="file"
        accept="image/*"
        style={{ display: "none" }}
        onChange={handleImageSelect}
      />

      {/* ===== 하단 ===== */}
      <div className="home-bottom-area">
        <div className="home-pick-bar">
          <button className="home-pick-btn" onClick={handleCameraClick}>
            <CameraIcon />
            <span>카메라</span>
          </button>

          <div className="home-pick-divider" />

          <button className="home-pick-btn" onClick={handleFileSelectClick}>
            <ImageIcon />
            <span>이미지 파일</span>
          </button>
        </div>

        <button
          className="home-analyze-btn"
          disabled={!selectedImage}
          onClick={handleAnalyze}
        >
          <AnalyzeIcon />
          <span>메뉴판 분석</span>
        </button>
      </div>
    </div>
  );
}
