Создай MVP веб-приложения для мониторинга Telegram-каналов и выявления трендов для магазина дизайнерских футболок в Санкт-Петербурге.


Цель приложения:
Собирать посты из выбранных Telegram-каналов, извлекать из них сущности через Natasha + GLiNER + словари, сохранять данные в Postgres, считать базовую статистику по трендам и показывать результат в веб-интерфейсе.

Технологический стек:

    * Python 3.11+
    * FastAPI
    * Postgres
    * SQLAlchemy
    * Alembic, если уместно
    * React + TypeScript
    * Telethon для Telegram API
    * Natasha
    * GLiNER
    * pandas
    * python-dotenv

Основные сущности данных:

1. channels
   Поля:

* id
* title
* username
* url
* category
* is_active
* created_at

2. posts
   Поля:

* id
* telegram_message_id
* channel_id
* post_date
* text
* views
* forwards
* reactions_count
* url
* created_at

3. entities
   Поля:

* id
* post_id
* entity_text
* normalized_text
* entity_type
* source
* confidence
* created_at

4. daily_entity_stats
   Поля:

* id
* date
* entity
* entity_type
* mentions_count
* channels_count
* total_views
* total_reactions
* growth_7d
* growth_30d
* trend_score

Функциональность MVP:

1. Управление каналами

    * Страница со списком Telegram-каналов.
    * Возможность добавить канал по username или URL.
    * Возможность отключить канал из мониторинга.

2. Сбор постов

    * Сбор последних N постов из активных каналов.
    * N задается пользователем, по умолчанию 10.
    * Не сохранять дубликаты по telegram_message_id + channel_id.
    * Сохранять текст, дату, просмотры, репосты, реакции, ссылку.

3. Извлечение сущностей

* Для каждого нового поста извлекать сущности через:
  * Natasha: люди, организации, локации.
  * GLiNER: бренд, персонаж, мем, игра, фильм, сериал, музыкант, событие, место в Санкт-Петербурге, визуальный стиль, субкультура.
  * словари: локальные темы СПб, районы, популярные мемные слова, визуальные стили.

* Для каждой сущности сохранять:
  * исходный текст,
  * нормализованный текст,
  * тип,
  * источник: natasha / gliner / dictionary,
  * confidence.

4. Словари
   Создать папку `dictionaries/`.
   Добавить JSON-файлы:
        * spb_places.json
        * local_themes.json
        * visual_styles.json
        * brands.json
        * memes.json

Пример структуры словаря:
[
{
"term": "Питер",
"normalized": "Санкт-Петербург",
"type": "location"
},
{
"term": "дождь",
"normalized": "питерский дождь",
"type": "local_theme"
}
]

5. Подсчет статистики

* Агрегировать сущности по дням.
* Считать:
  * mentions_count,
  * channels_count,
  * total_views,
  * total_reactions,
  * growth_7d,
  * growth_30d,
  * trend_score.

Простая формула trend_score:
    trend_score =
    mentions_count * 0.25 +
    channels_count * 0.2 +
    log(total_views + 1) * 0.2 +
    log(total_reactions + 1) * 0.15 +
    growth_7d * 0.2



6. Веб-интерфейс
    см. interface.md


7. Конфигурация
   В `.env.example`:
   TELEGRAM_API_ID=38568928
   TELEGRAM_API_HASH=2beb49a0525a29b18b3d71ae5518c4ad
   TELEGRAM_SESSION_NAME=trend_monitor

    Приложение должно запускаться на проде по такой же схеме как проект ../poputi
    Создай скрипты для запуска в папке ./scripts

8. Ограничения

* Приложение должно запускаться с помощью Docker.
* GPU не требуется.
* Скорость не важна, важна понятность кода.
* Добавь обработку ошибок.
* Добавь логирование.
* лучше пока сделать один микросервис 
* Не добавляй авторизацию.
* Сделай код расширяемым, чтобы позже можно было добавить OpenAI API для генерации дизайнерских брифов.


