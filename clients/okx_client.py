# clients/okx_client.py
import requests
import logging
from typing import List, Dict
from .base_client import MarketDataClient

logger = logging.getLogger(__name__)

# Единый формат -> OKX
BAR_MAP = {
    "1m": "1m", "5m": "5m", "15m": "15m", "30m": "30m",
    "1H": "1H", "2H": "2H", "4H": "4H", "6H": "6H", "12H": "12H",
    "1D": "1D", "1W": "1W", "1M": "1M",
}

# Длительность бара в миллисекундах (для вычисления close_time)
_BAR_MS = {
    "1m": 60_000, "5m": 300_000, "15m": 900_000, "30m": 1_800_000,
    "1H": 3_600_000, "2H": 7_200_000, "4H": 14_400_000,
    "6H": 21_600_000, "12H": 43_200_000,
    "1D": 86_400_000, "1W": 604_800_000, "1M": 2_592_000_000,
}


class OKXClient(MarketDataClient):
    name = "okx"
    BASE_URL = "https://www.okx.com/api/v5"

    def fetch_candles(self, inst_id: str, bar: str = "1H", limit: int = 100) -> List[Dict]:
        params = {
            "instId": inst_id,
            "bar": BAR_MAP.get(bar, bar),
            "limit": str(min(limit, 300)),  # OKX: максимум 300
        }
        try:
            response = requests.get(
                f"{self.BASE_URL}/market/candles",
                params=params,
                timeout=10,
            )
            response.raise_for_status()
            payload = response.json()

            if payload.get("code") != "0":
                logger.error(f"[OKX] {inst_id}: {payload.get('msg')}")
                return []

            bar_ms = _BAR_MS.get(bar, 3_600_000)
            # OKX отдаёт от новых к старым — инвертируем для единого формата
            return [
                {
                    "open_time": int(c[0]),
                    "close_time": int(c[0]) + bar_ms - 1,
                    "open": float(c[1]),
                    "high": float(c[2]),
                    "low": float(c[3]),
                    "close": float(c[4]),
                    "volume": float(c[5]),
                    "quote_volume": float(c[7]),
                    "trades": 0,  # OKX не возвращает trades в свечах
                }
                for c in reversed(payload.get("data", []))
            ]
        except Exception as e:
            logger.error(f"[OKX] Ошибка получения {inst_id}: {e}")
            return []

    def is_available(self) -> bool:
        try:
            r = requests.get(f"{self.BASE_URL}/public/time", timeout=5)
            return r.json().get("code") == "0"
        except Exception:
            return False