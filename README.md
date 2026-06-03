# Trend Monitor MVP

MVP веб-приложения для мониторинга Telegram-каналов и поиска трендов для магазина дизайнерских футболок в Санкт-Петербурге.

## Что внутри

- `backend/` FastAPI + SQLAlchemy + Alembic + Telethon + Natasha + GLiNER
- `frontend/` React + TypeScript + Vite
- `dictionaries/` локальные словари сущностей и тем
- `scripts/` локальные и прод-скрипты запуска
- `nginx/` прокси для схемы запуска, совместимой с `../poputi`

## Быстрый старт

1. Скопируйте `.env.example` в `.env`.
2. Запустите `./scripts/local-dev.sh`.
3. Откройте `http://127.0.0.1:3015/app`.

## Ограничения

- Для Telethon нужен валидный Telegram session login.
- Модель GLiNER скачивается при первом запуске, если ее нет в образе.
- Кнопка "Создать бриф" пока строит текстовый prompt без вызова OpenAI API.

