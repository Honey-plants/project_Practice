# ai/journal/food_journal_prompt.py
import json
from io import BytesIO
from PIL import Image
from typing import Any, Dict, List
from google import genai
from google.genai import types
import os
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("GOOGLE_API")

client = genai.Client(
    api_key=API_KEY
)

def journal_prompt(payload: Dict[str, Any]) -> str:
    template = payload["template"]
    member = payload["member"]
    reviews: List[Dict[str, Any]] = payload["reviews"]

    style = template.get("style", {})
    language = template.get("language", "en")


    return f"""
You are creating a SINGLE illustrated food journal page in a FUNNY “mock academic paper / magazine” style,
like a parody research poster (e.g., “Journal of Daily Studies”).

TARGET READER:
- International traveler in Korea
- Has dietary restrictions (allergies/vegan/etc.)
- Wants reassurance + practical ordering help

USER:
- nickname: {member.get("nickname")}
- gender: {member.get("gender")}
- country: {member.get("country")}
- dislike_tags: {member.get("dislike_tags")}
- item_ids (diet rules): {member.get("item_ids")}

REVIEWS (source of truth; do not invent extra visits):
1) {reviews[0]["review_title"]} — {reviews[0]["review_content"]}
2) {reviews[1]["review_title"]} — {reviews[1]["review_content"]}
3) {reviews[2]["review_title"]} — {reviews[2]["review_content"]}


OUTPUT (TEXT) REQUIREMENTS:
1) A parody “paper title” (1 line), in ALL CAPS or Title Case.
2) A tiny “subtitle” line like: “An Investigation into ...”
3) 3 short paragraphs (one per review). Each paragraph:
   - starts with a mini section header like “1. Introduction”, “2. Humerous Observation”, “3. Aftermath or Conclusion”
5) Provide 6 very short caption lines (5–8 words each) for the illustrator to place under images.


# IMAGE REQUIREMENTS:
# - Image is to be real-life photo style
# - Humerous Observation image can be illustrate
# - Image is LANDSCAPE orientation(wide poster/ newsletter) 
# - Aspect ratio: 16:9 or 3:2 (landscape) with high resolution, 1 complete page
# - VISUAL THEME:
#    - Warm, friendly, travel diary + newsletter + scrapbook aesthetic
#    - Cute illustrations of Korean food + restaurant / street food vibe
#    - Clean layout with readable text (not too text-heavy)
#    - SafeEat brand vibe: warm red/orange accents, cozy paper texture
# - TOP HEADER (must look like a classic newspaper/journal masthead like the reference image): 
#    - Centered big title: "Food Journal of SafeEat" 
#    - Small line above it: "Newsletter • Vol. 1 • Issue 1"
#    - Small line below it: "Safe meals in Korea for travelers with dietary restrictions"
#    - Use a serif / newspaper-style header typography and thin divider lines



# OUTPUT:
# - Generate ONE complete image

"""

def culture_journal(payload: Dict[str, Any]) -> str:
    template = payload["template"]
    member = payload["member"]
    reviews: List[Dict[str, Any]] = payload["reviews"]

    style = template.get("style", {})
    language = template.get("language", "en")

    return f"""
Create a single-page photo-based image that blends
the user’s Korean food experience with CURRENT TOP TRENDING Korean cultural trends.

This is NOT about K-pop specifically.
This is about “what Korea feels like right now.”

CONCEPT:
The food the user ate becomes a metaphor for a trending Korean issue,
social mood, or pop-culture wave.
- eg. user ate kimbab, it was in the scene of kpop demon hunter, blend that to user 

Examples of Korean “issues” to draw from:
- Viral shows, games, or fantasy archetypes (e.g. demon hunter, survivor, trainee)
- Internet humor and memes
- Seasonal habits (late-night eating, spicy food in winter, soup during stress)
- Youth culture, work culture, travel culture
- “Everyone in Korea is into this right now” energy

STORY RULES:
- The user is the main character
- Food is part of the story world
- Avoid naming real IPs directly
- Use metaphor and tone instead
- Use user information:
    - nickname: {member.get("nickname")}
    - gender: {member.get("gender")}
    - country: {member.get("country")}
    - dislike_tags: {member.get("dislike_tags")} ( if any)
    - item_ids (diet rules): {member.get("item_ids")} (if any)

FOOD → STORY BEHAVIOR:
Turn each eaten menu into a scene that connects to a Korean cultural “issue” or trend:
- memes, late-night food culture, convenience store vibes, work/school grind culture
- seasonal habits (hangover soup, winter comfort stews, spicy stress relief)
- viral fantasy archetypes (e.g., demon hunter / survivor / trainee) as metaphor
You MAY reference a “demon hunter craze” vibe, but DO NOT use real IP names or copyrighted character names.
- Users eaten menu has to be the FOOD in the story eg if they didnt eat food , dont include in the story
- Try to tell everything in an image not describe in long text to draw readers attention


TEXT STYLE:
- Short narrative blocks
- Cinematic but funny
- Not a review, not an ad
- dont divide into episodes 
- Use users review to get a hind of positive/negative idea toward the food they ate but DONT include any review content
    1) {reviews[0]["review_title"]} — {reviews[0]["review_content"]}
    2) {reviews[1]["review_title"]} — {reviews[1]["review_content"]}
    3) {reviews[2]["review_title"]} — {reviews[2]["review_content"]}

LAYOUT STYLE:
- Image is LANDSCAPE orientation(wide poster/ newsletter)
- Aspect ratio: 16:9 or 3:2 (landscape) with high resolution, 1 complete page
- Real-life photo collage
- Academic / magazine parody layout
- Section headers feel like episodes or chapters
- Character must be related to their country. eg. if from japan, has to be japanese looking character 

DO NOT:
- Mention restaurant ratings
- Quote reviews
- Explain app features directly
- Sound promotional
- create new concept like where they ate, what date they ate , 
- make up information like city, date they ate, etc as it will be provided in {payload} 

FINAL FEELING:
This journal should feel like:
“I didn’t just eat Korean food.
I accidentally became part of Korea’s current storyline.”
"I want to keep record of this image forever as it depicts the trip." 
Make viewers think:
'I want to eat like this in Korea'
'I want my food to turn into a story'
'I should use this app just to get this journal'

# OUTPUT:
# - Generate ONE complete image

"""

def generate_journal(journal_prompt):

    response = client.models.generate_content(
        model="gemini-2.5-flash-image",
        contents=journal_prompt,
        config=types.GenerateContentConfig(
            response_modalities=["IMAGE"]
        )
    )

    # 1. 응답에 후보(candidates)가 있고, 내용(content)이 있는지 먼저 확인
    if not response.candidates or not response.candidates[0].content:
        # 안전 필터 등으로 인해 차단된 경우
        print("경고: 모델이 이미지를 생성하지 못했습니다. (안전 필터 혹은 정책 위반 가능성)")

        # 차단 이유 확인 (디버깅용)
        if response.candidates and response.candidates[0].finish_reason:
            print(f"중단 이유: {response.candidates[0].finish_reason}")

        return None  # 에러 대신 None을 반환하여 프로그램이 멈추지 않게 함

    # 2. 내용이 있을 때만 parts에 접근
    for part in response.candidates[0].content.parts:
        if part.inline_data:
            return part.inline_data.data


    return None

if __name__ == "__main__":
    with open("mock_request.json", "r", encoding="utf-8") as f:
        data = json.load(f)

    logo = Image.open("logo.png").convert("RGBA")

    prompt = journal_prompt(data)
    # culture_prompt = culture_journal(data)

    image_bytes = generate_journal(prompt)
    if image_bytes is None:
        print("이미지 생성 실패")
        raise SystemExit(1)

    # ✅ PNG로 저장
    img = Image.open(BytesIO(image_bytes))
    out_path = "food_journal_1.png"
    img.save(out_path)
    print(f"✅ saved: {out_path}")
