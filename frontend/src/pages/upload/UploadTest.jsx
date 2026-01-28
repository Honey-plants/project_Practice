import React, { useContext, useState } from "react";
import { UploadContext } from "../../context/UploadContext";
import { MenuAssistantAPI } from "../../api/menuAssistantApi";
import { JournalAPI } from "../../api/journalApi";

export default function UploadTest() {
  const { stateUpload, uploadActions } = useContext(UploadContext);

  const [type, setType] = useState("review");
  const [file, setFile] = useState(null);
  const [ownerId, setOwnerId] = useState("");

  const [menuFile, setMenuFile] = useState(null);
  const [menuProfileText, setMenuProfileText] = useState("{\n  \"allergy_tags\": []\n}");
  const [menuResult, setMenuResult] = useState(null);
  const [menuError, setMenuError] = useState("");

  const [journalText, setJournalText] = useState(
    "{\n  \"journal_type\": \"journal\",\n  \"template\": {\n    \"language\": \"en\"\n  },\n  \"member\": {\n    \"nickname\": \"Alex\",\n    \"gender\": \"M\",\n    \"country\": \"US\",\n    \"dislike_tags\": [],\n    \"item_ids\": []\n  },\n  \"reviews\": [\n    {\n      \"review_title\": \"Great\",\n      \"review_content\": \"Loved the bibimbap.\"\n    },\n    {\n      \"review_title\": \"Okay\",\n      \"review_content\": \"Service was fine.\"\n    },\n    {\n      \"review_title\": \"Nice\",\n      \"review_content\": \"Would visit again.\"\n    }\n  ]\n}"
  );
  const [journalResult, setJournalResult] = useState(null);
  const [journalError, setJournalError] = useState("");

  const onUpload = async () => {
    if (!file) return;
    await uploadActions.upload({
      file,
      type,
      owner_id: ownerId ? Number(ownerId) : undefined,
    });
  };

  const onMenuEnqueue = async () => {
    setMenuError("");
    setMenuResult(null);
    if (!menuFile) {
      setMenuError("menu image file is required");
      return;
    }

    let profile = null;
    if (menuProfileText.trim()) {
      try {
        profile = JSON.parse(menuProfileText);
      } catch (e) {
        setMenuError("user_profile_json is invalid JSON");
        return;
      }
    }

    try {
      const res = await MenuAssistantAPI.enqueue({
        file: menuFile,
        userProfile: profile,
      });
      setMenuResult(res.data);
    } catch (e) {
      setMenuError(e?.response?.data?.detail || "menu enqueue failed");
    }
  };

  const onJournalEnqueue = async () => {
    setJournalError("");
    setJournalResult(null);
    let payload;
    try {
      payload = JSON.parse(journalText);
    } catch (e) {
      setJournalError("journal payload is invalid JSON");
      return;
    }

    try {
      const res = await JournalAPI.enqueue(payload);
      setJournalResult(res.data);
    } catch (e) {
      setJournalError(e?.response?.data?.detail || "journal enqueue failed");
    }
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