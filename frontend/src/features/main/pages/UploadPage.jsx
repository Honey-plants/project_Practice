import React, { useRef } from "react";
import { useNavigate } from "react-router-dom";
import { navigateToPreview } from "../../../common/utils/navigateToPreview";
import "./UploadPage.css";
import Header from "../../../common/components/ui/Header";
import axios from "axios";

export default function UploadPage() {
  const navigate = useNavigate();
  const inputRef = useRef(null);

  const TEST_URL = "/menu/upload"

  const handleFileChange = async (e) => {
    try {
      const file = e.target.files?.[0];
      if (!file) return;

      console.log("file :: ", file)

      const fd = new FormData();
      fd.append("image", file);
      fd.append("type", "review");

      console.log(fd.get("image"));
      console.log(fd.get("image")?.name);
      console.log(fd.data);

      const accessToken = sessionStorage.getItem("accessToken");

      // HttpOnly 쿠키 기반이면 이 방식이 정답 (JS로 토큰 못 읽음)
      // 서버가 쿠키 인증을 지원해야 함 (Authorization 헤더 대신 쿠키에서 토큰 읽기)
      const res = await axios.post(TEST_URL, fd, {
        withCredentials: true, // ✅ 쿠키 자동 전송
        headers: {
          Authorization: `Bearer ${accessToken}`,
        },
      });

      console.log("res :: ", res)
      console.log("menu analyze res :: ", res.data);

    } catch (err) {
      console.error("upload error :: ", err);
      alert("업로드 실패. 콘솔 로그 확인해줘.");
    } finally {
      e.target.value = ""; // 같은 파일 재선택 가능
    }
  };

  return (
    <main className="page upload-page container">
      <Header />
      <div className="upload-zone">
        <h2 className="font-4 upload-title font-bold">Upload Menu Image</h2>
        <input
          ref={inputRef}
          type="file"
          accept="image/*"
          className="upload-input-hidden"
          onChange={handleFileChange}
        />
        <button className="button big color-main" onClick={() => inputRef.current.click()}>
          Choose from Gallery
        </button>
      </div>
      <button className="button medium color-ghost" onClick={() => navigate(-1)}>
        Go Back
      </button>
    </main>
  );
}
