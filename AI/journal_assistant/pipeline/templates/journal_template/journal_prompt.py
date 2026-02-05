# AI/journal_assistant/pipeline/templates/journal_template/journal_prompt.py

from __future__ import annotations
from typing import Dict, Any, List


def build_journal_prompt(payload: Dict[str, Any]) -> str:
    """
    Build a funny / warm food journal prompt.
    This function ONLY returns prompt text.
    No model calls here.
    """

    member = payload.get("member", {})
    reviews: List[Dict[str, Any]] = payload.get("reviews", [])
    template = payload.get("template", {})
    allergies = payload.get("allergy_tags", {})

    nickname = member.get("nickname", "The traveler")
    country = member.get("country", "Unknown country")
    # allergies = member.get("item_ids", [])

    print("저널 데이터 체크 시작")

    print("11111 :: member_id :: ", member)


    print("저널 데이터 체크 종료")

    # 안전: 리뷰는 최대 3개만 사용
    reviews = reviews[:3]

    # 리뷰 요약 블록 생성
    review_blocks = []
    for i, r in enumerate(reviews, start=1):
        title = r.get("review_title", "Untitled meal")
        content = r.get("review_content", "")


        review_blocks.append(
            f"""
MEAL {i}:
- Title: {title}
- Notes: {content}
""".strip()
        )

    reviews_text = "\n\n".join(review_blocks)

    allergy_text = (
        ", ".join(allergies)
        if allergies
        else "No known allergy_tags"
    )

    return f"""
You are creating a SINGLE-PAGE PHOTO JOURNAL
written in a completely unserious “mock academic paper” style.

This should feel like:
- a fake research poster
- a parody sociology paper
- a university hallway bulletin board
that somehow turned into a food diary.

TONE:
- Extremely funny
- Confident nonsense
- Academic words used incorrectly but passionately
- Reads like a professor lost their mind in Korea

IMPORTANT STYLE RULES:
- This is NOT informative.
- This is NOT serious.
- This is NOT a travel guide.
- The goal is: people should laugh immediately just by looking at it.

KOREAN VIBE (light, not cringe):
- Casual Korea references are OK (late-night eating, small restaurants, confusing menus, kindness of staff)
- Do NOT explain Korea.
- Assume Korea is chaos but warm.

LANGUAGE:
- ENGLISH ONLY
- Short sentences.
- Caption-style writing.
- No long paragraphs.

STRUCTURE:
The journal has EXACTLY 3 SECTIONS.

--------------------------------------------------
SECTION 1 — INTRO / IDEA
--------------------------------------------------
SECTION TITLE (funny, academic-sounding):
Something like:
- “Initial Hypothesis: I Thought I Was Just Hungry”
- “Preliminary Assumptions Before Entering Korea”

CONTENT:
- 2 REAL-LIFE PHOTOS from the user (food / table / receipt / street food etc.)
- Under EACH photo, write ONE short caption.

CAPTION STYLE:
- Fake academic observation
- Slightly dramatic
- Mildly confused

Examples (vibe only, do not copy):
- “Figure 1. The moment I believed I understood the menu.”
- “Early evidence suggested this meal would be safe. This belief was incorrect.”

--------------------------------------------------
SECTION 2 — INVESTIGATION
--------------------------------------------------
SECTION TITLE:
Something like:
- “Field Research Conducted While Sitting Down”
- “Methods: Trusting the App With My Life”

CONTENT:
- 2 REAL-LIFE PHOTOS
- Each photo gets ONE caption.

CAPTION STYLE:
- Treat eating as scientific experimentation
- Overanalyze normal things
- Reference allergies / translation / ordering confusion casually

Examples (vibe only):
- “Figure 3. Allergy avoidance in its natural habitat.”
- “Data indicates the staff was kinder than expected.”

--------------------------------------------------
SECTION 3 — AFTERMATH
--------------------------------------------------
SECTION TITLE:
Something like:
- “Conclusions Drawn With a Full Stomach”
- “Post-Meal Reflections and Emotional Stability”

CONTENT:
- 2 REAL-LIFE PHOTOS
- One-line captions only.

CAPTION STYLE:
- Absurd confidence
- Fake conclusions
- Slight emotional closure

Examples (vibe only):
- “Figure 6. No peanuts detected. Peace achieved.”
- “Further research is recommended. Tomorrow.”

--------------------------------------------------
TEXT RULES (VERY IMPORTANT):
- NO restaurant names
- NO addresses
- NO dates
- NO hashtags
- NO emojis
- NO real academic citations
- Do NOT explain jokes

PHOTO RULES:
- Photos are REAL-LIFE user photos (do not stylize them)
- Do not redraw or replace photos
- Treat photos as documentary evidence

FINAL OUTPUT:
- ONE single-page journal layout
- 3 clearly separated sections
- Each section has:
  - A funny academic-style title
  - 2 photos
  - Very short captions only

This journal should feel like:
“I accidentally published my lunch as a research paper.”

""".strip()
