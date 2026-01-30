import React, { useContext, useState } from "react";
import { UploadContext } from "../../context/UploadContext";

export default function UploadTest() {
  const { stateUpload, uploadActions } = useContext(UploadContext);

  const [type, setType] = useState("review");
  const [file, setFile] = useState(null);
  const [ownerId, setOwnerId] = useState("");

  const onUpload = async () => {
    if (!file) return;
    await uploadActions.upload({
      file,
      type,
      owner_id: ownerId ? Number(ownerId) : undefined,
    });
  };

  return (
    <div style={{ padding: 16, maxWidth: 720 }}>
      <h2>Upload Test</h2>

      <div style={{ display: "grid", gap: 10 }}>
        <select value={type} onChange={(e) => setType(e.target.value)}>
          <option value="review">review</option>
          <option value="community">community</option>
          <option value="member">member</option>
        </select>

        <input
          value={ownerId}
          onChange={(e) => setOwnerId(e.target.value)}
          placeholder="owner_id (optional)"
        />

        <input type="file" onChange={(e) => setFile(e.target.files?.[0] || null)} />

        <button onClick={onUpload} disabled={stateUpload.uploading}>
          {stateUpload.uploading ? "Uploading..." : "Upload"}
        </button>
      </div>

      {stateUpload.error && <div className="errorBox">{stateUpload.error}</div>}
      {stateUpload.lastResult && (
        <pre className="card">{JSON.stringify(stateUpload.lastResult, null, 2)}</pre>
      )}
    </div>
  );
}