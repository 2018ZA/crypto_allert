"""
HTTP-роутер для графика: GET /api/chart.

`openapi_examples` в Query даёт в Swagger UI именованные примеры
запроса — пользователь выбирает один из пресетов, а не пишет вручную.
"""

import logging
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.schemas.chart import ChartResponse, ErrorResponse
from app.services.chart_service import get_chart_data
from app.db.session import get_db  # noqa: E402

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/chart", tags=["Chart"])


@router.get(
    "",
    response_model=ChartResponse,
    summary="Свечи + сигналы по часам",
    description=(
        "Возвращает OHLCV-свечи и сигналы осцилляторной системы за "
        "указанный период.\n\n"
        "**Как работает фильтр `signals`:**\n\n"
        "Массив свечей НЕ сужается — каждой точке ставится флаг "
        "`is_filtered_signal` (`true` — сигнал прошёл фильтр). "
        "Фронт использует этот флаг для маркеров на графике, "
        "а сами свечи отрисовывает полностью — чтобы график "
        "не терял контекст.\n\n"
        "**Без фильтра** (`signals` не передан) — `is_filtered_signal=true` "
        "для всех точек с непустым сигналом (включая `neutral`).\n\n"
        "**Поддерживаемые форматы фильтра:**\n"
        "- `?signals=buy,sell` (через запятую)\n"
        "- `?signals=buy&signals=sell` (повторяющийся параметр)\n"
        "- `?signals=strong%20buy` (с пробелом внутри)"
    ),
    response_description="Свечи и сигналы за указанный период (ASC по времени)",
    responses={
        200: {
            "model": ChartResponse,
            "description": "Успешный ответ (в том числе `points: []` при пустом диапазоне)",
        },
        400: {
            "model": ErrorResponse,
            "description": "Некорректные `symbol`, `period` или `signals`",
            "content": {
                "application/json": {
                    "examples": {
                        "bad_period": {
                            "summary": "Невалидный период",
                            "value": {"detail": "invalid period '2d'. allowed: ['1d', '12h', '1h', '4h', '6h']"},
                        },
                        "bad_symbol": {
                            "summary": "Невалидный символ",
                            "value": {"detail": "symbol must be alphanumeric (letters and digits only)"},
                        },
                        "too_many_signals": {
                            "summary": "Слишком много фильтров",
                            "value": {"detail": "too many signal filters (max 20)"},
                        },
                    }
                }
            },
        },
        422: {
            "description": "Ошибка валидации FastAPI (например, `symbol` пустой)",
        },
        500: {
            "model": ErrorResponse,
            "description": "Внутренняя ошибка сервера (детали — в логах)",
            "content": {
                "application/json": {
                    "example": {"detail": "internal server error"},
                }
            },
        },
    },
    operation_id="get_chart_data",
)
async def get_chart(
    response: Response,
    symbol: str = Query(
        ...,
        min_length=1,
        max_length=32,
        description="Тикер: базовый (`eth`, `btc`, `sol`) или полный (`ETHUSDT`)",
        openapi_examples={
            "base_ticker": {
                "summary": "Базовый тикер",
                "description": "Сервер разрешит `eth` → `ETHUSDT`",
                "value": "eth",
            },
            "full_ticker": {
                "summary": "Полный тикер",
                "description": "Точное совпадение без fallback",
                "value": "ETHUSDT",
            },
        },
    ),
    period: str = Query(
        "1d",
        description="Период выборки",
        openapi_examples={
            "last_hour":    {"summary": "1 час",  "value": "1h"},
            "last_4h":      {"summary": "4 часа", "value": "4h"},
            "last_6h":      {"summary": "6 часов","value": "6h"},
            "last_12h":     {"summary": "12 часов","value": "12h"},
            "last_day":     {"summary": "Сутки",  "value": "1d"},
        },
    ),
    signals: Optional[List[str]] = Query(
        None,
        description=(
            "Фильтр по силе сигнала. Поддерживает `?signals=buy,sell` "
            "и `?signals=buy&signals=sell`. "
            "Значения: `buy`, `sell`, `strong buy`, `strong sell`, `neutral`. "
            "Пусто = все сигналы."
        ),
        openapi_examples={
            "all": {
                "summary": "Без фильтра (все сигналы)",
                "value": None,
            },
            "buy_family": {
                "summary": "Только buy + strong buy",
                "value": ["buy", "strong buy"],
            },
            "sell_family": {
                "summary": "Только sell + strong sell",
                "value": ["sell", "strong sell"],
            },
            "strong_only": {
                "summary": "Только сильные сигналы",
                "value": ["strong buy", "strong sell"],
            },
        },
    ),
    db: AsyncSession = Depends(get_db),
) -> ChartResponse:
    """См. описание эндпоинта в декораторе."""
    try:
        data = await get_chart_data(
            db=db, symbol=symbol, period=period, signals=signals,
        )
        response.headers["Cache-Control"] = "public, max-age=30"
        return ChartResponse(**data)

    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    except Exception:
        logger.exception(
            "unexpected error in /api/chart: symbol=%r period=%r signals=%r",
            symbol, period, signals,
        )
        raise HTTPException(status_code=500, detail="internal server error")