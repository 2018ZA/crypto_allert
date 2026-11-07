"""
Pydantic-схемы ответа API графика.

Примеры заданы через `json_schema_extra` — они попадают в Swagger UI
как «Example Value» для каждой схемы и каждого поля.
"""

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field


class ChartPoint(BaseModel):
    """Одна свеча + сигнал осцилляторной системы."""

    # Примеры и описание уровня модели — в Swagger как блок "Examples"
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "timestamp": 1762430400000,
                "time": "2026-11-06T12:00:00Z",
                "open": 3450.12,
                "high": 3470.55,
                "low": 3440.10,
                "close": 3465.30,
                "volume": 1234.56,
                "signal": "buy",
                "score": 5.0,
                "has_signal": True,
                "is_filtered_signal": True,
            }
        }
    )

    timestamp: int = Field(
        ...,
        description="Unix ms (UTC) — совместимо с lightweight-charts и highcharts",
        examples=[1762430400000],
    )
    time: datetime = Field(
        ...,
        description="Время открытия свечи в UTC (ISO 8601)",
        examples=["2026-11-06T12:00:00Z"],
    )

    open: float = Field(..., description="Цена открытия", examples=[3450.12])
    high: float = Field(..., description="Максимум свечи", examples=[3470.55])
    low: float = Field(..., description="Минимум свечи", examples=[3440.10])
    close: float = Field(..., description="Цена закрытия", examples=[3465.30])
    volume: float = Field(..., description="Объём базового актива", examples=[1234.56])

    signal: Optional[str] = Field(
        None,
        description=(
            "Канонический сигнал: `buy` | `sell` | `strong buy` | "
            "`strong sell` | `neutral` | `null` (нет данных осцилляторов)"
        ),
        examples=["buy"],
    )
    score: Optional[float] = Field(
        None,
        description="overall_score из oscillator_data, диапазон −14..+14",
        examples=[5.0],
    )

    has_signal: bool = Field(
        False,
        description="True, если overall_signal непустой (включая neutral)",
        examples=[True],
    )
    is_filtered_signal: bool = Field(
        False,
        description=(
            "True, если сигнал прошёл текущий фильтр. "
            "Фронт использует ТОЛЬКО этот флаг для маркеров."
        ),
        examples=[True],
    )


class ChartResponse(BaseModel):
    """Полный ответ эндпоинта GET /api/chart."""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "symbol": "ETHUSDT",
                "interval": "1h",
                "period": "1d",
                "from_time": "2026-11-06T12:00:00Z",
                "to_time": "2026-11-07T12:00:00Z",
                "points_count": 24,
                "signal_points_count": 5,
                "points": [
                    {
                        "timestamp": 1762430400000,
                        "time": "2026-11-06T12:00:00Z",
                        "open": 3450.12, "high": 3470.55,
                        "low": 3440.10, "close": 3465.30,
                        "volume": 1234.56,
                        "signal": "buy", "score": 5.0,
                        "has_signal": True, "is_filtered_signal": True,
                    },
                    {
                        "timestamp": 1762434000000,
                        "time": "2026-11-06T13:00:00Z",
                        "open": 3465.30, "high": 3472.00,
                        "low": 3458.00, "close": 3460.10,
                        "volume": 987.65,
                        "signal": "neutral", "score": 1.0,
                        "has_signal": True, "is_filtered_signal": False,
                    },
                ],
            }
        }
    )

    symbol: str = Field(
        ...,
        description="Разрешённый символ (например, ETHUSDT для запроса `eth`)",
        examples=["ETHUSDT"],
    )
    interval: str = Field(
        "1h",
        description="Таймфрейм свечей (в текущей схеме БД — всегда `1h`)",
        examples=["1h"],
    )
    period: str = Field(
        ...,
        description="Запрошенный период: `1h` | `4h` | `6h` | `12h` | `1d`",
        examples=["1d"],
    )
    from_time: datetime = Field(
        ..., description="Начало диапазона (UTC)",
        examples=["2026-11-06T12:00:00Z"],
    )
    to_time: datetime = Field(
        ..., description="Конец диапазона (UTC)",
        examples=["2026-11-07T12:00:00Z"],
    )
    points_count: int = Field(..., description="Всего свечей в ответе", examples=[24])
    signal_points_count: int = Field(
        ..., description="Сколько точек прошло фильтр", examples=[5],
    )
    points: List[ChartPoint] = Field(
        ..., description="Свечи по возрастанию времени (ASC)",
    )


class ErrorResponse(BaseModel):
    """Стандартная ошибка FastAPI (HTTPException)."""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "detail": "invalid period '2d'. allowed: ['1d', '12h', '1h', '4h', '6h']"
            }
        }
    )

    detail: str = Field(..., description="Человекочитаемое описание ошибки")