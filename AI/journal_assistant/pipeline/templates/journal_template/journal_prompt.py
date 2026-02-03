from __future__ import annotations
from typing import Dict, Any, List


def build_journal_prompt(payload: Dict[str, Any]) -> str:

    member = payload.get("member", {})
    reviews: List[Dict[str, Any]] = payload.get("reviews", [])

    nickname = member.get("nickname", "The traveler")
    country = member.get("country", "Unknown country")
    gender = member.get("gender", "")
    allergies = member.get("item_ids", [])

    # 리뷰 요약 블록 생성
    review_blocks = []
    for i, r in enumerate(reviews, start=1):
        title = r.get("review_title", "Untitled meal")
        content = r.get("review_content", "")
        rating = r.get("rating", 0)
        review_blocks.append(
            f"""
MEAL {i}:
- Title: {title}
- Notes: {content}
- Rating: {rating}
""".strip()
        )

    reviews_text = "\n\n".join(review_blocks)

    allergy_text = (
        ", ".join(allergies)
        if allergies
        else "No known allergies"
    )

    return f"""
    {reviews_text}
    {allergy_text}
    {nickname}
    {country}
    {gender}
Create ONE single-page TRAVEL JOURNAL (landscape).

MAIN CHARACTER:
The USER is the main character, not the food.
Food is only evidence of the user’s travel adventure in Korea.

VISUAL PRIORITY (in order):
1) The traveler’s presence (hands, silhouette, back-of-head, shoes, coat sleeve)
2) Travel evidence in Korea (street signs, subway card, market aisle, night street, map scribbles)
3) Food photos as “proof” (supporting role)

CRITICAL PHOTO RULE:
- Use REAL-LIFE photography for all photos.
- Do NOT redraw photos.
- Do NOT cartoonize food.
- You MAY add hand-drawn doodles/annotations on top of photos.

PAGE FEEL:
- Looks like a personal scrapbook/journal page found in someone’s bag.
- Paper texture, tape corners, torn edges, imperfect alignment.
- Deadpan funny, overconfident, nonsense conclusions.

CONTENT (must include):
- 1 “Hero” travel photo panel (street / market / subway / night scene) as the biggest photo.
- 3–5 smaller photos surrounding it:
  - at least 1 food photo
  - at least 1 “ordering / menu confusion / receipt / app screen” photo
  - at least 1 “hands holding food / chopsticks / tray” photo (user presence)

USER REPRESENTATION RULES:
- The user must appear anonymously:
  - hands, torso, silhouette, or cropped face turned away
- Do not invent a specific identity or exact face.
- The traveler is a symbolic anonymous person.

TONE:
- Mock academic + diary + nonsense
- Overconfident and wrong
- Short lines only
- No paragraphs

TEXT (minimal):
- Only short caption-style notes.
- Use fake academic words incorrectly.
- Keep it shareable and instantly funny.

ABSURD ASSOCIATIONS (allowed, no explanations):
- Gukbap → pig → strength → spiritual upgrade
- Tteokbokki → lava → bravery certification
- Mandu → pillow → emotional stability regained
Never explain why.

STRUCTURE (3 blocks on the page, not big headings):
BLOCK 1: “HYPOTHESIS”
- 1 travel photo + 1 short caption
BLOCK 2: “FIELDWORK”
- 2–3 mixed photos (travel + food + app/receipt) + short captions
BLOCK 3: “CONCLUSION”
- 1–2 photos + 1–2 absurd confident conclusion lines

DO NOT:
- No restaurant names, addresses, dates
- No ratings
- No hashtags/emojis
- No long text

FINAL FEEL:
This is a Korea travel journal page where the viewer laughs because
the traveler is taking their own eating journey way too seriously.

""".strip()
