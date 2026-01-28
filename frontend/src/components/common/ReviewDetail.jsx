function formatDate(v) {
  if (!v) return "-";
  const d = new Date(v);
  if (Number.isNaN(d.getTime())) return String(v);
  return d.toLocaleString();
}

function renderStars(rating) {
  const n = Number(rating);
  if (!Number.isFinite(n)) return "-";
  const clamped = Math.max(0, Math.min(5, Math.round(n)));
  return "★".repeat(clamped) + "☆".repeat(5 - clamped);
}

export function ReviewDetail({ review }) {
  if (!review) return null;

  const { title, content, rating, createdAt, images, menuNames, location } = review;

  return (
    <div
      style={{
        border: "1px solid #eee",
        borderRadius: 12,
        padding: 16,
        display: "grid",
        gap: 14,
      }}
    >
      {/* 제목 */}
      <div>
        <h1 style={{ margin: 0, fontSize: 22 }}>{title || "(no title)"}</h1>
        <div style={{ marginTop: 6, fontSize: 13, opacity: 0.8 }}>
          <span>작성일: {formatDate(createdAt)}</span>
          {location ? <span style={{ marginLeft: 10 }}>지역: {location}</span> : null}
        </div>
      </div>

      {/* 별점 */}
      <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
        <strong>별점</strong>
        <span>{renderStars(rating)}</span>
        {rating != null ? <span style={{ opacity: 0.8 }}>({rating}/5)</span> : null}
      </div>

      {/* 메뉴명(영수증 디텍트 결과) */}
      <div>
        <strong>영수증 메뉴</strong>
        {menuNames?.length ? (
          <div style={{ display: "flex", flexWrap: "wrap", gap: 8, marginTop: 8 }}>
            {menuNames.map((m, idx) => (
              <span
                key={`${m}-${idx}`}
                style={{
                  padding: "6px 10px",
                  border: "1px solid #ddd",
                  borderRadius: 999,
                  fontSize: 13,
                }}
              >
                {m}
              </span>
            ))}
          </div>
        ) : (
          <div style={{ marginTop: 8, opacity: 0.7 }}>-</div>
        )}
      </div>

      {/* 이미지 0~3 */}
      <div>
        <strong>사진</strong>
        {images?.length ? (
          <div
            style={{
              marginTop: 10,
              display: "grid",
              gridTemplateColumns: "repeat(3, 1fr)",
              gap: 10,
            }}
          >
            {images.slice(0, 3).map((src, idx) => (
              <div
                key={`${src}-${idx}`}
                style={{
                  border: "1px solid #eee",
                  borderRadius: 10,
                  overflow: "hidden",
                  aspectRatio: "1 / 1",
                  background: "#fafafa",
                }}
              >
                <img
                  src={src}
                  alt={`review-${idx}`}
                  style={{ width: "100%", height: "100%", objectFit: "cover" }}
                  onError={(e) => {
                    e.currentTarget.style.display = "none";
                  }}
                />
              </div>
            ))}
          </div>
        ) : (
          <div style={{ marginTop: 8, opacity: 0.7 }}>-</div>
        )}
      </div>

      {/* 내용 */}
      <div>
        <strong>리뷰 내용</strong>
        <div style={{ marginTop: 8, whiteSpace: "pre-wrap", lineHeight: 1.5 }}>
          {content || "-"}
        </div>
      </div>
    </div>
  );
}
