"""
Конфигурация OpenAPI/Swagger: теги, серверы, описание, UI-параметры.

`openapi()` расширяет автогенерируемую схему FastAPI:
- добавляет `servers` (dev/staging/prod) для переключения в Swagger UI;
- описывает теги (группы эндпоинтов);
- добавляет общие примеры для `422` (валидация FastAPI).
"""

from typing import Any, Dict

from fastapi import FastAPI
from fastapi.openapi.utils import get_openapi


# ---------------------------------------------------------------------------
# Метаданные верхнего уровня — отображаются в шапке Swagger UI
# ---------------------------------------------------------------------------
API_TITLE = "Crypto Alert API"
API_VERSION = "1.0.0"
API_DESCRIPTION = """
REST API для графика криптовалют и сигналов осцилляторной системы.

## Возможности
- **Свечи OHLCV** по часам (1h) с сигналами осцилляторов
- **Фильтр по силе сигнала:** `buy`, `sell`, `strong buy`, `strong sell`, `neutral`
- **Гибкие периоды:** 1h, 4h, 6h, 12h, 1d
- **Fallback по символу:** `eth` → `ETHUSDT` (если полного тикера нет в БД)

## Соглашения
- Все времена — **UTC**.
- `timestamp` — Unix ms (совместимо с lightweight-charts / highcharts).
- В ответе `points` всегда **по возрастанию времени** (ASC).
- `is_filtered_signal` — единственный флаг, по которому фронт ставит маркеры.
  Свечи при фильтрации не сужаются, чтобы график сохранял контекст.

## Коды ошибок
- `400` — невалидные `symbol` / `period` / `signals`
- `422` — ошибка валидации FastAPI (пустой `symbol`, слишком длинная строка)
- `500` — внутренняя ошибка (детали — в логах сервера)
"""

# Теги: порядок в списке = порядок в Swagger UI
TAGS_METADATA = [
    {
        "name": "Chart",
        "description": (
            "Данные для графика: свечи, сигналы, скоринг. "
            "Один запрос — один график с маркерами сигналов."
        ),
        "externalDocs": {
            "description": "Документация по осцилляторам",
            "url": "https://www.investopedia.com/terms/o/oscillator.asp",
        },
    },
]

# Серверы: позволяют переключать base URL прямо в Swagger UI
SERVERS = [
    {"url": "http://localhost:8000", "description": "Локальная разработка"},
    {"url": "https://staging.example.com", "description": "Staging"},
    {"url": "https://api.example.com", "description": "Production"},
]


def custom_openapi(app: FastAPI) -> Dict[str, Any]:
    """
    Возвращает расширенную OpenAPI-схему. Кэшируется в `app.openapi_schema`,
    чтобы не пересобирать на каждый запрос `/openapi.json`.
    """
    if app.openapi_schema:
        return app.openapi_schema

    schema = get_openapi(
        title=API_TITLE,
        version=API_VERSION,
        description=API_DESCRIPTION,
        routes=app.routes,
        tags=TAGS_METADATA,
        servers=SERVERS,
    )

    # Добавляем стандартный пример 422 (FastAPI не всегда его заполняет).
    components = schema.setdefault("components", {})
    schemas = components.setdefault("schemas", {})
    schemas.setdefault(
        "HTTPValidationError",
        {
            "type": "object",
            "properties": {
                "detail": {
                    "type": "array",
                    "items": {"$ref": "#/components/schemas/ValidationError"},
                }
            },
        },
    )
    schemas.setdefault(
        "ValidationError",
        {
            "type": "object",
            "properties": {
                "loc": {
                    "type": "array",
                    "items": {"anyOf": [{"type": "string"}, {"type": "integer"}]},
                },
                "msg": {"type": "string"},
                "type": {"type": "string"},
            },
            "required": ["loc", "msg", "type"],
        },
    )

    app.openapi_schema = schema
    return schema