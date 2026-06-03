# Trend Monitor MVP

MVP веб-приложения для мониторинга Telegram-каналов и поиска трендов для магазина дизайнерских футболок в Санкт-Петербурге.

## Что внутри

- `backend/` FastAPI + SQLAlchemy + Alembic + Natasha + GLiNER
- `trends_telegram/` отдельный микросервис для Telegram API и хранения Telethon session
- `frontend/` React + TypeScript + Vite
- `dictionaries/` локальные словари сущностей и тем
- `scripts/` локальные и прод-скрипты запуска
- `nginx/` прокси для схемы запуска, совместимой с `../poputi`

## Быстрый старт

1. Скопируйте `.env.example` в `.env`.
2. Запустите `./scripts/local-dev.sh`.
3. Откройте `http://127.0.0.1:3015/app`.

## Ограничения

- Для `trends-telegram` нужен валидный Telegram session login.
- Модель GLiNER скачивается при первом запуске, если ее нет в образе.
- После сбора данных приложение пытается автоматически создать «Футболку дня» через OpenAI API и сохранить результат в S3.
- «Футболка дня» требует настроенных `OPENAI_API_KEY` и S3-переменных.
