import React from "react";
import MenuUpload from "../components/menu/MenuUpload";

export default function Home() {
  return (
    <div style={{ padding: 16, maxWidth: 980, margin: "0 auto" }}>
      <h2 style={{ marginTop: 0 }}>Menu Assistant</h2>
      <p style={{ color: "#555", marginTop: 4 }}>
        메뉴판 이미지를 업로드하면 보정 이미지 + 최종 번역 JSON(final_translated.json)을 표시합니다.
      </p>
      <MenuUpload />
    </div>
  );
}
