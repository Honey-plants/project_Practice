from dataclasses import dataclass

@dataclass(frozen=True)
class TempKeys:
    base_prefix: str      # 예: "menu/{run_id}" or "receipt/{upload_id}"
    input_key: str        # 예: "menu/{run_id}/input.jpg"
    result_key: str       # 예: "menu/{run_id}/result.json" (menu만)

def menu_temp_keys(run_id: str, ext: str = "jpg") -> TempKeys:
    base = f"menu/{run_id}"
    return TempKeys(
        base_prefix=base,
        input_key=f"{base}/input.{ext}",
        result_key=f"{base}/result.json",
    )

def receipt_temp_keys(upload_id: str, ext: str = "jpg") -> TempKeys:
    base = f"receipt/{upload_id}"
    return TempKeys(
        base_prefix=base,
        input_key=f"{base}/input.{ext}",
        result_key=f"{base}/ocr.json",
    )
