export default function PreviewLayer({
  previewUrl,
  onRetry,
  onConfirm
}) {
  return (
    <div className="preview-root">
      <img
        src={previewUrl}
        alt="preview"
        className="preview-image"
      />

      <div className="preview-controls">
        <button onClick={onRetry}>
          
        </button>

        <button onClick={onConfirm}>
          Comfirm
        </button>
      </div>
    </div>
  );
}