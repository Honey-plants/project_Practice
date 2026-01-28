from __future__ import annotations

import argparse
import json
from pathlib import Path

from AI.review.app.pipeline.step_3_normalize.run_normalize import normalize_receipt_data

def main():
    p = argparse.ArgumentParser(description="Step3 Normalize Receipt (from OCR JSON)")
    p.add_argument("ocr_json", type=Path, help="Path to ocr_result.json")
    p.add_argument("--y-threshold", type=int, default=15)
    p.add_argument("--out", type=Path, default=Path("debug/step3"), help="output directory")
    args = p.parse_args()

    args.out.mkdir(parents=True, exist_ok=True)

    data = json.loads(args.ocr_json.read_text(encoding="utf-8"))

    # support both formats
    ocr_items = data["items"] if isinstance(data, dict) else data

    result = normalize_receipt_data(
        ocr_items,
        y_threshold=args.y_threshold,
    )

    # ✅ save for step4
    out_json = args.out / "step3_normalize_result.json"
    out_json.write_text(
        json.dumps(result, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    print("✅ saved:", out_json)
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()