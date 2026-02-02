import React from "react";
import { useNavigate } from "react-router-dom";
import ReviewCreateForm from "../../components/review/ReviewCreateForm";

export default function ReviewCreate() {
  const navigate = useNavigate();

  const handleCreated = (reviewData) => {
    console.log("리뷰 생성 완료:", reviewData);

<<<<<<< HEAD
    // 2초 후 리뷰 리스트 페이지로 이동
    setTimeout(() => {
      navigate("/review");
    }, 2000);
=======
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

  const x = extracted?.coords?.x;
  const y = extracted?.coords?.y;
  const location = x && y ? `${x},${y}` : undefined;

  const menu_name =
    extracted?.menu_en?.[0] ||
    extracted?.menu_name?.[0] ||
    undefined;

  const payload = {
    receipt_id: receiptId,
    title,
    content,
    rating,
    location,
    menu_name,
    images,
>>>>>>> ff58bf2fa2de9f6c7fe8dcd3838ce113f8a97ee3
  };

  console.log("[ReviewCreateInline] payload to send:", {
    ...payload,
    images: (images || []).map((f) => ({ name: f.name, size: f.size, type: f.type })),
  });

  setLoadingCreate(true);
  try {
    const r = await ReviewAPI.createFromReceipt(payload);

    setMsg("리뷰 생성 완료");
    onCreated?.(r.data);

    setReceiptFile(null);
    setReceiptId(null);
    setExtracted(null);
    setTitle("");
    setContent("");
    setRating(5);
    setImages([]);
  } catch (e) {
    console.error("[ReviewCreateInline] create failed:", e);
    console.error("[ReviewCreateInline] status:", e?.response?.status);
    console.error("[ReviewCreateInline] response:", e?.response?.data);
    setErr(e?.response?.data?.detail || e?.message || "리뷰 생성 실패");
  } finally {
    setLoadingCreate(false);
  }
};

  return (
    <div style={{
      minHeight: "100vh",
      background: "linear-gradient(135deg, #667eea 0%, #764ba2 100%)",
      padding: "40px 20px"
    }}>
      <div style={{
        maxWidth: "900px",
        margin: "0 auto"
      }}>
        {/* 상단 헤더 */}
        <div style={{
          marginBottom: "24px",
          textAlign: "center",
          color: "white"
        }}>
          <h1 style={{
            fontSize: "36px",
            fontWeight: "800",
            margin: "0 0 8px 0",
            textShadow: "2px 2px 4px rgba(0,0,0,0.2)"
          }}>
            🍽️ 새 리뷰 작성
          </h1>
          <p style={{
            fontSize: "16px",
            margin: 0,
            opacity: 0.95
          }}>
            영수증을 업로드하고 맛있었던 경험을 공유해주세요!
          </p>
        </div>

        {/* 뒤로가기 버튼 */}
        <div style={{ marginBottom: "16px" }}>
          <button
            onClick={() => navigate("/review")}
            style={{
              padding: "10px 20px",
              background: "rgba(255, 255, 255, 0.2)",
              color: "white",
              border: "1px solid white",
              borderRadius: "8px",
              cursor: "pointer",
              fontWeight: "600",
              fontSize: "14px",
              backdropFilter: "blur(10px)",
              transition: "all 0.2s"
            }}
            onMouseEnter={(e) => {
              e.currentTarget.style.background = "rgba(255, 255, 255, 0.3)";
            }}
            onMouseLeave={(e) => {
              e.currentTarget.style.background = "rgba(255, 255, 255, 0.2)";
            }}
          >
            ← 리뷰 목록으로 돌아가기
          </button>
        </div>

        {/* 리뷰 작성 폼 */}
        <ReviewCreateForm onCreated={handleCreated} />
      </div>
    </div>
  );
}
