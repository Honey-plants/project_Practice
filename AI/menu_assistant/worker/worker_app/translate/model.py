# menu_assistant/worker/worker_app/translate/model.py
from __future__ import annotations

import json
from typing import Any, Dict, List, Optional

from menu_assistant.worker.worker_app.llm.client import (
    Gemini25FlashClient,
    GeminiClientConfig,
)


class GeminiTranslateClient:
    """
    Step6 Translation wrapper
    - .env / API key 로딩은 translate/client.py(Gemini25FlashClient)에 전적으로 위임
    - 여기서는 "프롬프트 전달 -> JSON 파싱 -> final item 번역 결과 스키마 정리"만 담당
    """

    def __init__(
        self,
        cfg: Optional[GeminiClientConfig] = None,
        dotenv_path: Optional[str] = None,
        max_dotenv_up: int = 8,
    ) -> None:
        self.cfg = cfg or GeminiClientConfig()
        self._client = Gemini25FlashClient(
            config=self.cfg,
            dotenv_path=dotenv_path,
            max_dotenv_up=max_dotenv_up,
        )

    # ------------------------------------------------------------
    # Low-level call
    # ------------------------------------------------------------
    @staticmethod
    def _strip_code_fence(s: str) -> str:
        t = (s or "").strip()
        if t.startswith("```"):
            t = t.split("\n", 1)[-1]
            if t.endswith("```"):
                t = t.rsplit("```", 1)[0]
        return t.strip()

    def generate_json(self, *, system: str, user: str) -> Dict[str, Any]:
        """
        Gemini 호출 -> JSON(dict) 파싱해서 반환.
        client.py는 raw text(JSON expected)를 반환하고,
        여기서 파싱/검증을 담당.
        """
        text = self._client.generate_json(system=system, user=user)
        if not text:
            raise RuntimeError("[translate/model] Empty response from Gemini.")

        cleaned = self._strip_code_fence(text)

        try:
            return json.loads(cleaned)
        except Exception as e:
            raise RuntimeError(
                "[translate/model] Failed to parse JSON from Gemini.\n"
                f"Raw: {text[:1000]}\n"
                f"Cleaned: {cleaned[:1000]}\n"
                f"Error: {e}"
            )

    # ------------------------------------------------------------
    # Final.json translation helpers
    # ------------------------------------------------------------
    @staticmethod
    def extract_required_fields_from_final_item(item: Dict[str, Any]) -> Dict[str, Any]:
        """
        final.json의 item 1개에서 번역에 필요한 필수 필드만 추출.
        - item_id, match: 그대로 유지(passthrough)
        - menu/risk/comment: 번역 대상(필수)
        """
        item_id = item.get("item_id")
        match = item.get("match")

        menu = item.get("menu") or {}
        risk = item.get("risk") or {}

        payload = {
            "item_id": item_id,
            "match": match,
            "menu": {
                "menu_name_ko": (menu.get("menu_name_ko") or "").strip(),
                "menu_description_ko": (menu.get("menu_description_ko") or "").strip(),
            },
            "risk": {
                "risk_level": (risk.get("risk_level") or "").strip(),
                "risk_description_ko": (risk.get("risk_description_ko") or "").strip(),
            },
            # comment는 final.json 구조상 risk 안에 있음
            "comment_ko": (risk.get("comment") or "").strip(),
        }

        if payload["item_id"] is None:
            raise ValueError("[translate/model] item_id is missing in final item.")
        if payload["match"] is None:
            raise ValueError("[translate/model] match is missing in final item.")
        if payload["risk"] is None:
            raise ValueError("[translate/model] match is missing in final item.")

        return payload

    def translate_final_item(
        self,
        *,
        item: Dict[str, Any],
        system_prompt: str,
        user_prompt: str,
    ) -> Dict[str, Any]:
        """
        Step6가 최종 조립하기 좋게,
        - item_id, match는 그대로
        - menu/risk/comment 번역 결과만 en 필드로 반환
        """
        src = self.extract_required_fields_from_final_item(item)
        out = self.generate_json(system=system_prompt, user=user_prompt)

        menu_out = out.get("menu", {}) if isinstance(out, dict) else {}
        risk_out = out.get("risk", {}) if isinstance(out, dict) else {}

        comment_out = out.get("comment", {}) if isinstance(out, dict) else {}

        result = {
            "item_id": src["item_id"],
            "match": src["match"],
            "menu": {
                "menu_name_en": (menu_out.get("menu_name_en") or "").strip(),
                "menu_description_en": (menu_out.get("menu_description_en") or "").strip(),
            },
            "risk": {
                "risk_level": src["risk"]["risk_level"],  # 원본 유지
                "risk_description_en": (risk_out.get("risk_description_en") or "").strip(),
            },
            "comment": {
                #  schema에 맞는 경로
                "comment_en": (comment_out.get("comment_en") or "").strip(),
                #  LLM이 주면 그거 쓰고, 없으면 원본(=risk.comment) fallback
                "comment_ko": (
                        (comment_out.get("comment_ko") or "").strip()
                        or (src.get("comment_ko") or "").strip()
                ),
            },
        }
        return result

    def translate_final_items_batch(
        self,
        *,
        items: List[Dict[str, Any]],
        build_prompts_fn,
    ) -> List[Dict[str, Any]]:
        """
        Step6에서 items 루프 돌 때 쓰기 편하도록 제공.
        build_prompts_fn(item) -> (system_prompt, user_prompt)
        """
        results: List[Dict[str, Any]] = []
        for it in items:
            system_p, user_p = build_prompts_fn(it)
            results.append(self.translate_final_item(item=it, system_prompt=system_p, user_prompt=user_p))
        return results
