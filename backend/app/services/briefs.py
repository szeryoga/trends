from __future__ import annotations

from app.schemas.trend import TrendDetail


def build_brief_prompt(trend: TrendDetail) -> str:
    examples = "\n".join(f"- [{item.channel_title}] {item.text[:240]}" for item in trend.posts[:10])
    related = ", ".join(trend.related_entities[:10]) or "нет"
    growth = trend.stats[-1].growth_7d if trend.stats else None
    growth_text = "new trend" if growth is None and trend.stats and trend.stats[-1].new_trend else f"{growth or 0:.1f}%"
    return f"""Ты арт-директор бренда дизайнерских футболок.

Тренд:
{trend.entity}

Тип:
{trend.entity_type}

Рост:
{growth_text}

Связанные сущности:
{related}

Примеры упоминаний:
{examples}

Сформируй:
1. Описание тренда
2. Целевую аудиторию
3. 5 идей для принтов
4. Рекомендации по стилю
5. Риск нарушения авторских прав
"""

