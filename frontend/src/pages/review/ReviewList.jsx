import React, { useContext, useEffect, useState, useMemo } from "react";
import { Link } from "react-router-dom";
import { ReviewContext } from "../../context/ReviewContext";
import ReviewItem from "../../components/review/ReviewCard";
import { MetaAPI } from "../../api/metaApi";

export default function ReviewList() {
  const { stateReview, reviewActions } = useContext(ReviewContext);

  const [categories, setCategories] = useState([]);
  const [selectedCategory, setSelectedCategory] = useState(null);
  const [selectedItemIds, setSelectedItemIds] = useState([]); // 선택된 아이템 ID 배열

  // 카테고리 및 리뷰 목록 로드
  useEffect(() => {
    reviewActions.fetchList();
    loadCategories();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const loadCategories = async () => {
    try {
      const response = await MetaAPI.getActiveRestrictions();
      // 응답 형식: { etag: "...", data: [...] }
      const list = response.data?.data || response.data || [];
      setCategories(list);
    } catch (e) {
      console.error("카테고리 로드 실패:", e);
    }
  };

  // 아이템 선택/해제 토글
  const toggleItem = (itemId) => {
    setSelectedItemIds(prev => {
      if (prev.includes(itemId)) {
        return prev.filter(id => id !== itemId);
      } else {
        return [...prev, itemId];
      }
    });
  };

  // 필터 초기화
  const clearFilters = () => {
    setSelectedCategory(null);
    setSelectedItemIds([]);
  };

  // 선택된 카테고리 또는 아이템으로 필터링된 리뷰 목록
  const filteredReviews = useMemo(() => {
    return stateReview.list.filter((review) => {
      const reviewItems = review.review_items || [];

      // review_items가 문자열인 경우 배열로 변환
      const reviewItemIds = typeof reviewItems === 'string'
        ? reviewItems.split(',').map(id => Number(id.trim()))
        : Array.isArray(reviewItems)
        ? reviewItems.map(id => Number(id))
        : [];

      // 특정 아이템이 선택되었으면 해당 아이템이 포함된 리뷰만 표시 (다중 선택 가능)
      if (selectedItemIds.length > 0) {
        return selectedItemIds.some(itemId => reviewItemIds.includes(itemId));
      }

      // 아이템이 선택되지 않고 카테고리만 선택되었으면 해당 카테고리의 아이템 중 하나라도 포함된 리뷰 표시
      if (selectedCategory) {
        const categoryItems = selectedCategory.items || [];
        return categoryItems.some(catItem =>
          reviewItemIds.includes(catItem.item_id)
        );
      }

      // 필터가 없으면 전체 표시
      return true;
    });
  }, [stateReview.list, selectedCategory, selectedItemIds]);

  const displayList = filteredReviews;
  const displayLoading = stateReview.loading;
  const displayError = stateReview.error;

  return (
    <div style={{ padding: "20px", maxWidth: "1200px", margin: "0 auto" }}>
      <div style={{
        display: "flex",
        justifyContent: "space-between",
        alignItems: "center",
        marginBottom: "24px"
      }}>
        <h1 style={{ margin: 0, fontSize: "28px", fontWeight: "700" }}>리뷰 목록</h1>
        <Link
          to="/review/new"
          style={{
            padding: "10px 20px",
            background: "#007bff",
            color: "white",
            textDecoration: "none",
            borderRadius: "6px",
            fontWeight: "600",
            transition: "background 0.2s"
          }}
          onMouseEnter={(e) => e.currentTarget.style.background = "#0056b3"}
          onMouseLeave={(e) => e.currentTarget.style.background = "#007bff"}
        >
          + 새 리뷰 작성
        </Link>
      </div>

      {/* 필터링 섹션 */}
      {categories.length > 0 && (
        <div style={{
          marginBottom: "24px",
          padding: "20px",
          background: "white",
          borderRadius: "12px",
          border: "1px solid #e0e0e0"
        }}>
          {/* 헤더 */}
          <div style={{
            display: "flex",
            justifyContent: "space-between",
            alignItems: "center",
            marginBottom: "16px"
          }}>
            <div style={{ fontWeight: "600", fontSize: "16px" }}>
              필터
            </div>
            {(selectedCategory || selectedItemIds.length > 0) && (
              <button
                onClick={clearFilters}
                style={{
                  padding: "6px 12px",
                  background: "#f8f9fa",
                  color: "#dc3545",
                  border: "1px solid #dc3545",
                  borderRadius: "6px",
                  cursor: "pointer",
                  fontSize: "13px",
                  fontWeight: "500"
                }}
              >
                필터 초기화
              </button>
            )}
          </div>

          {/* 카테고리 선택 */}
          <div style={{ marginBottom: "16px" }}>
            <div style={{ marginBottom: "10px", fontWeight: "600", fontSize: "14px", color: "#495057" }}>
              카테고리
            </div>
            <div style={{ display: "flex", gap: "8px", flexWrap: "wrap" }}>
              <button
                onClick={() => {
                  setSelectedCategory(null);
                }}
                style={{
                  padding: "8px 16px",
                  background: !selectedCategory ? "#007bff" : "#f8f9fa",
                  color: !selectedCategory ? "white" : "#333",
                  border: "1px solid " + (!selectedCategory ? "#007bff" : "#ddd"),
                  borderRadius: "20px",
                  cursor: "pointer",
                  fontSize: "14px",
                  fontWeight: "500",
                  transition: "all 0.2s"
                }}
              >
                전체
              </button>
              {categories.map((category) => (
                <button
                  key={category.category_id}
                  onClick={() => {
                    setSelectedCategory(category);
                  }}
                  style={{
                    padding: "8px 16px",
                    background: selectedCategory?.category_id === category.category_id ? "#007bff" : "#f8f9fa",
                    color: selectedCategory?.category_id === category.category_id ? "white" : "#333",
                    border: "1px solid " + (selectedCategory?.category_id === category.category_id ? "#007bff" : "#ddd"),
                    borderRadius: "20px",
                    cursor: "pointer",
                    fontSize: "14px",
                    fontWeight: "500",
                    transition: "all 0.2s"
                  }}
                >
                  {category.category_label_ko || category.category_label_en || `Category #${category.category_id}`}
                </button>
              ))}
            </div>
          </div>

          {/* 선택된 아이템 표시 (다른 카테고리에서 선택한 것들) */}
          {selectedItemIds.length > 0 && (
            <div style={{ marginBottom: "16px" }}>
              <div style={{ marginBottom: "10px", fontWeight: "600", fontSize: "14px", color: "#495057" }}>
                선택된 항목 ({selectedItemIds.length}개)
              </div>
              <div style={{ display: "flex", gap: "8px", flexWrap: "wrap" }}>
                {categories.flatMap(cat => cat.items || [])
                  .filter(item => selectedItemIds.includes(item.item_id))
                  .map((item) => (
                    <button
                      key={item.item_id}
                      onClick={() => toggleItem(item.item_id)}
                      style={{
                        padding: "6px 14px",
                        background: "#28a745",
                        color: "white",
                        border: "1px solid #28a745",
                        borderRadius: "16px",
                        cursor: "pointer",
                        fontSize: "13px",
                        fontWeight: "500",
                        transition: "all 0.2s"
                      }}
                    >
                      ✓ {item.item_label_ko || item.item_label_en || `Item #${item.item_id}`}
                    </button>
                  ))}
              </div>
            </div>
          )}

          {/* 아이템 선택 (카테고리가 선택되었을 때만 표시) */}
          {selectedCategory && selectedCategory.items && selectedCategory.items.length > 0 && (
            <div>
              <div style={{ marginBottom: "10px", fontWeight: "600", fontSize: "14px", color: "#495057" }}>
                {selectedCategory.category_label_ko || selectedCategory.category_label_en} 세부 항목
              </div>
              <div style={{ display: "flex", gap: "8px", flexWrap: "wrap" }}>
                {selectedCategory.items.map((item) => {
                  const isSelected = selectedItemIds.includes(item.item_id);
                  return (
                    <button
                      key={item.item_id}
                      onClick={() => toggleItem(item.item_id)}
                      style={{
                        padding: "6px 14px",
                        background: isSelected ? "#28a745" : "#fff",
                        color: isSelected ? "white" : "#495057",
                        border: "1px solid " + (isSelected ? "#28a745" : "#ced4da"),
                        borderRadius: "16px",
                        cursor: "pointer",
                        fontSize: "13px",
                        fontWeight: "500",
                        transition: "all 0.2s"
                      }}
                    >
                      {isSelected && "✓ "}
                      {item.item_label_ko || item.item_label_en || `Item #${item.item_id}`}
                    </button>
                  );
                })}
              </div>
            </div>
          )}

          {/* 필터 상태 표시 */}
          {(selectedCategory || selectedItemIds.length > 0) && (
            <div style={{
              marginTop: "16px",
              padding: "10px 12px",
              background: "#e7f3ff",
              borderRadius: "6px",
              fontSize: "13px",
              color: "#004085"
            }}>
              {selectedItemIds.length > 0 ? (
                <>
                  <strong>{selectedItemIds.length}개 항목</strong>이 선택된 리뷰를 표시 중
                </>
              ) : selectedCategory ? (
                <>
                  "<strong>{selectedCategory.category_label_ko || selectedCategory.category_label_en}</strong>" 카테고리의 리뷰를 표시 중
                </>
              ) : null}
            </div>
          )}
        </div>
      )}

      {displayError && (
        <div style={{
          padding: "16px",
          background: "#fee",
          color: "#c00",
          borderRadius: "8px",
          marginBottom: "20px",
          border: "1px solid #fcc"
        }}>
          <strong>오류 발생:</strong> {displayError}
        </div>
      )}

      {displayLoading && (
        <div style={{
          textAlign: "center",
          padding: "80px 20px",
          fontSize: "18px",
          color: "#666"
        }}>
          <div style={{
            display: "inline-block",
            width: "40px",
            height: "40px",
            border: "4px solid #f3f3f3",
            borderTop: "4px solid #007bff",
            borderRadius: "50%",
            animation: "spin 1s linear infinite"
          }}></div>
          <div style={{ marginTop: "16px" }}>로딩 중...</div>
        </div>
      )}

      {!displayLoading && displayList.length === 0 && (
        <div style={{
          textAlign: "center",
          padding: "80px 20px",
          color: "#999",
          background: "#f8f9fa",
          borderRadius: "8px"
        }}>
          <div style={{ fontSize: "48px", marginBottom: "16px" }}>📝</div>
          <div style={{ fontSize: "18px", marginBottom: "8px" }}>아직 리뷰가 없습니다</div>
          <div style={{ fontSize: "14px" }}>첫 번째 리뷰를 작성해보세요!</div>
        </div>
      )}

      <div style={{
        display: "grid",
        gridTemplateColumns: "repeat(auto-fill, minmax(280px, 1fr))",
        gap: "24px"
      }}>
        {displayList.map((review) => (
          <ReviewItem
            key={review.review_id || review.id}
            review={review}
          />
        ))}
      </div>
    </div>
  );
}