# clients/base_client.py
from abc import ABC, abstractmethod
from typing import List, Dict


class MarketDataClient(ABC):
    """Единый интерфейс источника рыночных данных."""

    name: str = "base"

    @abstractmethod
    def fetch_candles(self, inst_id: str, bar: str = "1H", limit: int = 100) -> List[Dict]:
        """
        Возвращает список свечей в стандартном формате, отсортированный
        по возрастанию open_time:
        [
            {
                'open_time': int,      # ms
                'close_time': int,     # ms
                'open': float,
                'high': float,
                'low': float,
                'close': float,
                'volume': float,
                'quote_volume': float,
                'trades': int,         # 0, если источник не отдаёт
            },
            ...
        ]
        """
        ...

    @abstractmethod
    def is_available(self) -> bool:
        """Проверка доступности источника (например, пингом)."""
        ...