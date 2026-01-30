import { useEffect } from "react";
import { createPortal } from "react-dom";
import styles from "../../styles/Modal.module.css";

export default function Modal({
  isOpen = false,
  onClose,
  onConfirm,
  message,
  title,
  children
}) {
  useEffect(() => {
    if (!isOpen) return;

    const originalOverflow = document.body.style.overflow;
    document.body.style.overflow = "hidden";

    return () => {
      document.body.style.overflow = originalOverflow;
    };
  }, [isOpen]);

  if (!isOpen) return null;

  return createPortal(
    <div className={styles.modalBackdrop} onClick={onClose}>
      <div className={styles.modal} onClick={(e) => e.stopPropagation()}>
        {title && (
          <div className={styles.modalHeader}>
            <div className={styles.modalTitle}>{title}</div>
            <button type="button" className={styles.modalCloseBtn} onClick={onClose}>✕</button>
          </div>
        )}

        <div className={styles.modalContent}>
          {children ? (
            children
          ) : (
            <>
              <p>{message}</p>
              <div className={styles.modalActions}>
                <button type="button" onClick={onClose}>Cancel</button>
                <button type="button" onClick={onConfirm}>Confirm</button>
              </div>
            </>
          )}
        </div>
      </div>
    </div>,
    document.body
  );
}