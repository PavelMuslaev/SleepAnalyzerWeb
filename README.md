# SleepAnalyzer — Анализатор данных сна

Веб-приложение для загрузки CSV с данными носимых устройств, анализа временных рядов, визуализации и выдачи рекомендаций.

## Быстрый старт
1. Клонируйте репозиторий.
2. Установите зависимости: `uv sync`
3. Запустите: `python app.py`
4. Откройте в браузере: `http://127.0.0.1:5000`
5. Загрузите файл из папки `test_data/` или свой CSV, соответствующий формату.

## Формат CSV
Файл должен иметь колонки (разделитель запятая):
- `date` (YYYY-MM-DD)
- `sleep_start` (HH:MM)
- `sleep_end` (HH:MM)
- `deep_sleep_minutes`
- `light_sleep_minutes`
- `rem_minutes`
- `awakenings` (целое число)

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