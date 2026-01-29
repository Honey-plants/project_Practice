# backend/app/features/meta/service.py
from __future__ import annotations

from typing import Dict, List
from sqlalchemy import select, func
from sqlalchemy.orm import Session

from backend.app.models.restrictions.category import Category
from backend.app.models.restrictions.item import Item


def get_restrictions_etag_meta(db: Session, only_active: bool = True) -> str:
    """
    ETag 생성용 메타:
    - category 최신 updated_at
    - item 최신 updated_at
    - category count / item count
    이 4개가 안 바뀌면 "실질적으로 동일 리소스"로 보고 304 처리.
    """

    cat_q = select(Category)
    item_q = select(Item)

    if only_active:
        cat_q = cat_q.where(Category.category_active.is_(True))
        item_q = item_q.where(Item.item_active.is_(True))

    cat_max = db.execute(select(func.max(Category.category_update)).select_from(cat_q.subquery())).scalar_one_or_none()
    item_max = db.execute(select(func.max(Item.item_update)).select_from(item_q.subquery())).scalar_one_or_none()

    cat_cnt = db.execute(select(func.count()).select_from(cat_q.subquery())).scalar_one()
    item_cnt = db.execute(select(func.count()).select_from(item_q.subquery())).scalar_one()

    cat_max_s = cat_max.isoformat(sep=" ", timespec="seconds") if cat_max else "null"
    item_max_s = item_max.isoformat(sep=" ", timespec="seconds") if item_max else "null"

    # Weak ETag 추천: 바이트단위 동일성보다 "버전" 목적
    return f'W/"cat:{cat_max_s}|item:{item_max_s}|cc:{cat_cnt}|ic:{item_cnt}|active:{int(only_active)}"'


def get_categories_with_items(db: Session, only_active: bool = True) -> List[dict]:
    """
    카테고리 + 아이템 전체를 내려줄 payload 생성.
    - N+1 방지: items 전체 1번 조회 후 category_id로 묶기
    """
    cat_stmt = select(Category).order_by(Category.category_id.asc())
    item_stmt = select(Item).order_by(
        Item.category_id.asc(),
        Item.item_id.asc(),
    )

    if only_active:
        cat_stmt = cat_stmt.where(Category.category_active.is_(True))
        item_stmt = item_stmt.where(Item.item_active.is_(True))

    categories = db.execute(cat_stmt).scalars().all()
    items = db.execute(item_stmt).scalars().all()

    bucket: Dict[int, list] = {}
    for it in items:
        bucket.setdefault(it.category_id, []).append(it)

    result: List[dict] = []
    for c in categories:
        result.append(
            {
                "category_id": c.category_id,
                "category_label_ko": c.category_label_ko,
                "category_label_en": c.category_label_en,
                "category_active": bool(c.category_active),
                "items": [
                    {
                        "item_id": it.item_id,
                        "item_label_ko": it.item_label_ko,
                        "item_label_en": it.item_label_en,
                        "category_id": it.category_id,
                        "item_active": bool(it.item_active),
                    }
                    for it in bucket.get(c.category_id, [])
                ],
            }
        )

    return result