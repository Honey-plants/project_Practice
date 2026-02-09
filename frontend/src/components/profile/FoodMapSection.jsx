import { useState, useEffect } from "react";
import styles from "./Section.module.css";
import mapStyles from "./FoodMapSection.module.css";

/**
 * FoodMapSection
 * template2(map)로 생성된 '먹거리 지도' 이미지를 표시
 * 1) localStorage에 저장된 이미지 URL을 우선 사용
 * 2) communities prop에서 저장된 community_id와 매칭하여 최신 image_urls 사용 (fallback)
 */
export default function FoodMapSection({ communities = [] }) {
  const [imageUrl, setImageUrl] = useState(null);

  useEffect(() => {
    const url = localStorage.getItem("foodmap_image_url");
    if (url) setImageUrl(url);

    // 다른 탭/컴포넌트에서 갱신될 때 반영
    const onStorage = (e) => {
      if (e.key === "foodmap_image_url") {
        setImageUrl(e.newValue);
      }
    };
    window.addEventListener("storage", onStorage);

    // 같은 탭 내 갱신 감지 (커스텀 이벤트)
    const onUpdate = () => {
      const url = localStorage.getItem("foodmap_image_url");
      if (url) setImageUrl(url);
    };
    window.addEventListener("foodmap-updated", onUpdate);

    return () => {
      window.removeEventListener("storage", onStorage);
      window.removeEventListener("foodmap-updated", onUpdate);
    };
  }, []);

  // communities prop에서 저장된 community_id로 매칭하여 최신 이미지 URL 사용
  useEffect(() => {
    if (imageUrl || !communities.length) return;

    const savedId = localStorage.getItem("foodmap_community_id");
    if (savedId) {
      const match = communities.find(
        (c) => String(c.community_id) === savedId
      );
      if (match?.image_urls?.[0]) {
        setImageUrl(match.image_urls[0]);
        localStorage.setItem("foodmap_image_url", match.image_urls[0]);
        return;
      }
    }

    // community_id도 없으면 community_type === "map" 으로 시도
    const mapCommunity = communities.find((c) => c.community_type === "map");
    if (mapCommunity?.image_urls?.[0]) {
      setImageUrl(mapCommunity.image_urls[0]);
      localStorage.setItem("foodmap_image_url", mapCommunity.image_urls[0]);
      localStorage.setItem("foodmap_community_id", String(mapCommunity.community_id));
    }
  }, [communities, imageUrl]);

  if (!imageUrl) return null;

  return (
    <div className={styles.section}>
      <div className={styles.header}>
        <h3 className={styles.title}>Food map</h3>
      </div>
      <div className={mapStyles.mapImageWrap}>
        <img
          src={imageUrl}
          alt="먹거리 지도"
          className={mapStyles.mapImage}
        />
      </div>
    </div>
  );
}
