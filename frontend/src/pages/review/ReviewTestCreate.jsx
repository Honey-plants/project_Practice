import React, { useState } from "react";
import ReviewTest from "../../components/review/ReviewTest"

export default function ReviewPage() {
  const [openCreate, setOpenCreate] = useState(false);

  return (
    <div style={{ padding: 16 }}>
      <div style={{ display: "flex", justifyContent: "space-between" }}>
        <h2>Review</h2>
        <button onClick={() => setOpenCreate((v) => !v)}>
          등록
        </button>
      </div>

      {openCreate && (
        <div style={{ marginBottom: 16 }}>
          <ReviewTest
            onCreated={() => {
              // TODO: 리스트 reload 로직 연결
              setOpenCreate(false);
            }}
          />
        </div>
      )}

      {/* 기존 리뷰 리스트 컴포넌트 */}
      {/* <ReviewList /> */}
    </div>
  );
}
