import { useContext, useEffect, useMemo } from "react";
import { MetaContext } from "../../context/MetaContext";
import RestrictionsPicker from "../restrictions/RestrictionsPicker";
import styles from "./Section.module.css";

/**
 * RestrictionsSection
 * 내가 선택한 제한 아이템 섹션 (읽기 전용)
 */
export default function RestrictionsSection({ selectedIds }) {
  const { stateMeta, metaActions } = useContext(MetaContext);

  // active True 카테고리/아이템
  const categories = useMemo(() => stateMeta?.restrictions || [], [stateMeta?.restrictions]);

  // 새로고침 직후 meta가 비어있으면 1회 로드 (active만)
  useEffect(() => {
    if (!stateMeta?.loading && (categories || []).length === 0) {
      metaActions?.refresh?.({ force: true });
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  return (
    <div className={styles.section}>
      <div className={styles.header}>
        <h3 className={styles.title}>
          Restricted information of my choice
        </h3>
      </div>

      {stateMeta?.loading && (
        <div className={styles.loading}>
          information loading...
        </div>
      )}

      {stateMeta?.error && (
        <div className={styles.errorBox}>
          {stateMeta.error}
        </div>
      )}

      <RestrictionsPicker
        categories={categories}
        selectedIds={selectedIds}
        mode="view"
        onlyActive={true}
      />
    </div>
  );
}
