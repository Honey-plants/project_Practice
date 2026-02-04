from sqlalchemy import text
import json

SQL = text("""
SELECT JSON_OBJECT(
  'member_id', :member_id,
  'categories', COALESCE(
    (
      SELECT JSON_ARRAYAGG(
        JSON_OBJECT(
          'category_id', t.category_id,
          'category_active', t.category_active,
          'category_label_en', t.category_label_en,
          'category_label_ko', t.category_label_ko,
          'items', t.items
        )
      )
      FROM (
        SELECT
          c.category_id,
          MAX(c.category_active)   AS category_active,
          MAX(c.category_label_en) AS category_label_en,
          MAX(c.category_label_ko) AS category_label_ko,
          JSON_ARRAYAGG(
            JSON_OBJECT(
              'item_id', i.item_id,
              'category_id', i.category_id,
              'item_active', i.item_active,
              'item_label_en', i.item_label_en,
              'item_label_ko', i.item_label_ko
            )
          ) AS items
        FROM member_restrictions mr
        JOIN restriction_items i ON i.item_id = mr.item_id
        JOIN restriction_category c ON c.category_id = i.category_id
        WHERE mr.member_id = :member_id
          AND c.category_active = 1
          AND i.item_active = 1
        GROUP BY c.category_id
      ) t
    ),
    JSON_ARRAY()
  ),
  'dislike', COALESCE(
    (
      SELECT CAST(rd.dislike_tag AS JSON)
      FROM restriction_dislike rd
      WHERE rd.member_id = :member_id
      LIMIT 1
    ),
    JSON_ARRAY()
  )
) AS result_json
""")

def build_user_profile_payload(db, member_id: int) -> dict:
    row = db.execute(SQL, {"member_id": member_id}).scalar()
    data = json.loads(row) if isinstance(row, str) else (row or {})

    categories = data.get("categories", []) or []
    dislike = data.get("dislike", []) or []

    allergy_tags = []
    religion = []

    for c in categories:
        cid = c.get("category_id")
        items = c.get("items", []) or []

        if cid == 1:  # Allergy
            allergy_tags = [
                it.get("item_label_en")
                for it in items
                if it.get("item_label_en")
            ]

        elif cid == 2:  # Religion
            # 1개만 쓰고 싶으면 이렇게
            val = items[0].get("item_label_en") if items else None
            religion = [val] if val else []

    return {
        "allergy_tags": allergy_tags,       # 없으면 []
        "avoid_foods": list(dislike),       # 없으면 []
        "religion": religion,               # 없으면 []
    }