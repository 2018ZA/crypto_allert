# clients/binance_client.py
import requests
import logging
from typing import List, Dict
from .base_client import MarketDataClient

logger = logging.getLogger(__name__)

# Единый формат -> Binance (таймфреймы в нижнем регистре)
BAR_MAP = {
    "1m": "1m", "5m": "5m", "15m": "15m", "30m": "30m",
    "1H": "1h", "2H": "2h", "4H": "4h", "6H": "6h", "12H": "12h",
    "1D": "1d", "1W": "1w", "1M": "1M",
}


class BinanceClient(MarketDataClient):
    name = "binance"
    BASE_URL = "https://api.binance.com/api/v3"

    def fetch_candles(self, inst_id: str, bar: str = "1H", limit: int = 100) -> List[Dict]:
        params = {
            "symbol": inst_id,
            "interval": BAR_MAP.get(bar, bar.lower()),
            "limit": min(limit, 1000),
        }
        try:
            response = requests.get(f"{self.BASE_URL}/klines", params=params, timeout=10)
            response.raise_for_status()

            # Binance уже отдаёт от старых к новым
            return [
                {
                    "open_time": int(c[0]),
                    "close_time": int(c[6]),
                    "open": float(c[1]),
                    "high": float(c[2]),
                    "low": float(c[3]),
                    "close": float(c[4]),
                    "volume": float(c[5]),
                    "quote_volume": float(c[7]),
                    "trades": int(c[8]),
                }
                for c in response.json()
            ]
        except Exception as e:
            logger.error(f"[Binance] Ошибка получения {inst_id}: {e}")
            return []

    def is_available(self) -> bool:
        try:
            r = requests.get(f"{self.BASE_URL}/ping", timeout=5)
            return r.status_code == 200
        except Exception:
            return False