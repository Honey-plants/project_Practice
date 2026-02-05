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
        final.json item 1개에서 번역에 필요한 최소 필드만 추출.
        - Step06 STRICT-FLAT을 기본으로 지원
        - 레거시(중첩 menu/risk)도 fallback으로 지원
        - match는 번역에 필요 없으므로 FLAT에서는 없어도 OK
        """
        if not isinstance(item, dict):
            raise ValueError("[translate/model] final item must be a dict.")

        item_id = item.get("item_id")
        if item_id is None:
            raise ValueError("[translate/model] item_id is missing in final item.")

        # ✅ match는 번역에 불필요. 없으면 {}로 처리 (STRICT-FLAT 호환)
        match = item.get("match")
        if not isinstance(match, dict):
            match = {}

        # 레거시 fallback
        menu = item.get("menu") if isinstance(item.get("menu"), dict) else {}
        risk = item.get("risk") if isinstance(item.get("risk"), dict) else {}

        # ✅ prompt.py가 쓰는 "루트 3필드" 우선
        menu_description_ko = (item.get("menu_description_ko") or menu.get("menu_description_ko") or "").strip()
        risk_description_ko = (item.get("risk_description_ko") or risk.get("risk_description_ko") or "").strip()

        comment_ko = (item.get("comment_ko") or "").strip()
        if not comment_ko:
            staff_list = risk.get("staff_comment_ko") or []
            if isinstance(staff_list, list):
                comment_ko = "\n".join([str(x).strip() for x in staff_list if str(x).strip()])
        if not comment_ko:
            comment_ko = (risk.get("comment") or "").strip()

        # ✅ translate/prompt.py는 루트 3필드만 사용하므로, 여기서도 flat로 반환
        return {
            "item_id": item_id,
            "match": match,  # 호환용(있어도/없어도 무관)
            "menu_description_ko": menu_description_ko,
            "risk_description_ko": risk_description_ko,
            "comment_ko": comment_ko,
        }

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

        # ✅ Case A) prompt.py가 요구하는 "루트 3키" 응답

        if isinstance(out, dict) and set(out.keys()) == {
            "menu_description_en",
            "risk_description_en",
            "comment_en",
            }:

            return {
                "menu_description_en": (out.get("menu_description_en") or "").strip(),
                "risk_description_en": (out.get("risk_description_en") or "").strip(),
                "comment_en": (out.get("comment_en") or "").strip(),
                }

        # ✅ Case B) (레거시) 중첩 객체 응답도 호환
        menu_out = out.get("menu", {}) if isinstance(out, dict) else {}
        risk_out = out.get("risk", {}) if isinstance(out, dict) else {}
        comment_out = out.get("comment", {}) if isinstance(out, dict) else {}

        # Step06 schema(3키)에 맞춰 정규화해서 반환

        return {
            "menu_description_en": (menu_out.get("menu_description_en") or "").strip(),
            "risk_description_en": (risk_out.get("risk_description_en") or "").strip(),
            "comment_en": (comment_out.get("comment_en") or "").strip(),
            }

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
