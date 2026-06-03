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
- После сбора данных страница «Футболка дня» показывает самый хайповый тренд и автоматически собранный бриф для принта.
- «Футболка дня» требует настроенных `OPENAI_API_KEY` и S3-переменных.
- Кнопка "Создать бриф" пока строит текстовый prompt без вызова OpenAI API.

## Инициализация Telegram session

Для первого запуска Telethon нужно один раз авторизовать Telegram session. В Docker-режиме session хранится в отдельном volume и переживает рестарты контейнера.

Запуск:

```bash
docker compose run --rm trends-telegram python -m app.auth_cli
```

Команда спросит телефон, код из Telegram и при необходимости пароль 2FA. После успешной авторизации можно запускать сбор постов обычной кнопкой в интерфейсе.
