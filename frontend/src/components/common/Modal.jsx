export default function Modal({
  isOpen = true,
  onClose,
  onConfirm,
  message,
  title,
  children
}) {
  if (!isOpen) return null;

  const overlayStyle = {
    position: "fixed",
    inset: 0,
    background: "rgba(0,0,0,0.5)",
    display: "flex",
    justifyContent: "center",
    alignItems: "center",
    zIndex: 9999,
  };

  const modalStyle = {
    background: "#fff",
    padding: 20,
    borderRadius: 10,
    minWidth: 320,
    maxWidth: 720,
    width: "90%",
  };

  return (
    <div style={overlayStyle} onClick={onClose}>
      <div style={modalStyle} onClick={(e) => e.stopPropagation()}>
        {(title || !children) && (
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
            <div style={{ fontWeight: 700 }}>{title || "Confirm"}</div>
            <button type="button" onClick={onClose}>✕</button>
          </div>
        )}

        <div style={{ marginTop: 12 }}>
          {/* ✅ ProfilePage: children(폼) 렌더 */}
          {children ? (
            children
          ) : (
            <>
              <p>{message}</p>
              <div style={{ display: "flex", justifyContent: "flex-end", gap: 8, marginTop: 16 }}>
                <button type="button" onClick={onClose}>Cancel</button>
                <button type="button" onClick={onConfirm}>Confirm</button>
              </div>
            </>
          )}
        </div>
      </div>
    </div>
  );
}