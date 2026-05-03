# SleepAnalyzer — Анализатор данных сна

Веб-приложение для загрузки CSV с данными носимых устройств, анализа временных рядов, визуализации и выдачи рекомендаций.

## Быстрый старт
1. Клонируйте репозиторий.
2. Установите зависимости: `uv sync`
3. Запустите: `python app.py`
4. Откройте в браузере: `http://127.0.0.1:5000`
5. Загрузите файл из папки `test_data/` или свой CSV, соответствующий формату.

## Формат CSV
Обязательные колонки:
- `date` (YYYY-MM-DD)
- `sleep_start`, `sleep_end` (HH:MM)
- `deep_sleep_minutes`, `light_sleep_minutes`, `rem_minutes` (float)
- `awakenings` (int)

Опциональные колонки (для расширенного анализа):
- `heart_rate_avg`, `hr_variability_avg`, `respiratory_rate_avg`, `movement_index`, `sleep_latency_minutes`, `sleep_quality_rating` (float/int)
- **`age`** (int) – возраст пользователя
- **`gender`** (M/F) – пол пользователя

Если указаны возраст и пол, приложение автоматически использует персонализированные нормы сна при расчёте Sleep Score и формировании рекомендаций.

## Структура проекта
- `app.py` — точка входа веб-приложения
- `config.py` — конфигурация
- `domain/` — бизнес-логика и модели
- `adapters/` — загрузка CSV
- `visualization/` — построение графиков (Plotly)
- `templates/` — HTML-шаблоны (Bootstrap 5)
- `static/` — статика
- `test_data/` — пример данных

## Технологии
- Python 3.10+
- Flask
- Plotly
- NumPy
- Bootstrap 5 (CDN)