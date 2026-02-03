import json
from pathlib import Path
from typing import Optional, Dict, Any

from AI.journal_assistant.pipeline.orchestrator import run_orchestrator

def main():
    payload = json.loads(Path("AI/journal_assistant/pipeline/mock_request_journal.json").read_text(encoding="utf-8"))

    img_bytes = run_orchestrator(payload)

    out = Path("debug_out.png")
    out.write_bytes(img_bytes)
    print("saved:", out)

if __name__ == "__main__":
    main()
