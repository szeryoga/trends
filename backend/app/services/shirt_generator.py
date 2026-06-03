from __future__ import annotations

import base64
import io
import json

from openai import OpenAI
from PIL import Image
from sqlalchemy import desc, select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.models.models import ShirtDesign
from app.schemas.shirt import ShirtDesignRead, ShirtOfDayResponse
from app.services.briefs import build_brief_prompt
from app.services.storage import upload_bytes_to_s3
from app.services.trend_service import get_trend_detail, list_trends_data


def _get_openai_client() -> OpenAI:
    settings = get_settings()
    if not settings.openai_api_key:
        raise RuntimeError("OPENAI_API_KEY is not configured.")
    return OpenAI(api_key=settings.openai_api_key)


def _build_text_assets(brief_prompt: str) -> tuple[str, str]:
    settings = get_settings()
    client = _get_openai_client()
    response = client.responses.create(
        model=settings.openai_text_model,
        input=[
            {
                "role": "system",
                "content": (
                    "You create concise production-ready outputs for a T-shirt design pipeline. "
                    "Return strict JSON with keys description and image_prompt."
                ),
            },
            {
                "role": "user",
                "content": (
                    "Using the brief below, produce JSON. "
                    "description: 2 short Russian sentences about the final T-shirt design. "
                    "image_prompt: detailed English prompt for an apparel graphic mockup-free centered T-shirt print concept. "
                    "Avoid text-heavy compositions, brand logos, watermarks, and copyrighted characters.\n\n"
                    f"{brief_prompt}"
                ),
            },
        ],
    )
    output_text = (getattr(response, "output_text", "") or "").strip()
    if output_text.startswith("```"):
        output_text = output_text.strip("`")
        if output_text.startswith("json"):
            output_text = output_text[4:].strip()
    try:
        payload = json.loads(output_text)
        return str(payload["description"]).strip(), str(payload["image_prompt"]).strip()
    except Exception:
        description = output_text[:500].strip() or "Дизайн опирается на самый быстрорастущий локальный тренд и адаптирован под принт на футболке."
        image_prompt = (
            "Premium streetwear T-shirt print concept, centered composition, transparent clean background style, "
            "bold graphic silhouette, poster-grade contrast, no mockup, no text-heavy layout. Brief:\n"
            f"{brief_prompt}"
        )
        return description, image_prompt


def _generate_webp_bytes(image_prompt: str) -> bytes:
    settings = get_settings()
    client = _get_openai_client()
    result = client.images.generate(
        model=settings.openai_image_model,
        prompt=image_prompt,
        size=settings.openai_image_size,
    )
    image_base64 = result.data[0].b64_json
    raw = base64.b64decode(image_base64)
    image = Image.open(io.BytesIO(raw)).convert("RGB")
    buffer = io.BytesIO()
    image.save(buffer, format="WEBP", quality=92)
    return buffer.getvalue()


def generate_shirt_of_day(db: Session) -> ShirtDesign:
    trends = list_trends_data(db, days=7, limit=1)
    if not trends:
        raise RuntimeError("No trends available for shirt generation.")
    top_trend = trends[0]
    trend_detail = get_trend_detail(db, top_trend["entity"])
    brief_prompt = build_brief_prompt(trend_detail)
    description, image_prompt = _build_text_assets(brief_prompt)
    webp_bytes = _generate_webp_bytes(image_prompt)
    key, url = upload_bytes_to_s3(webp_bytes, folder="shirts-of-day", extension="webp", content_type="image/webp")
    design = ShirtDesign(
        trend_entity=trend_detail.entity,
        trend_entity_type=trend_detail.entity_type,
        trend_score=float(top_trend["trend_score"]),
        trend_growth_7d=top_trend["growth_7d"],
        brief_prompt=brief_prompt,
        description=description,
        image_s3_key=key,
        image_url=url,
    )
    db.add(design)
    db.commit()
    db.refresh(design)
    return design


def get_shirt_of_day_payload(db: Session) -> ShirtOfDayResponse:
    items = list(db.scalars(select(ShirtDesign).order_by(desc(ShirtDesign.created_at)).limit(21)).all())
    current = items[0] if items else None
    history = items[1:21] if len(items) > 1 else []
    return ShirtOfDayResponse(
        current=ShirtDesignRead.model_validate(current, from_attributes=True) if current else None,
        history=[ShirtDesignRead.model_validate(item, from_attributes=True) for item in history],
    )
