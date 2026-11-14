# clients/okx_client.py
import requests
import logging
from typing import List, Dict, Optional
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
            # OKX /market/candles возвращает незакрытую свечу с confirm="0".
            # Фильтруем: только закрытые (confirm=="1"), иначе look-ahead bias.
            data = payload.get("data") or []
            data = [row for row in data if len(row) > 8 and row[8] == "1"]
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

    def fetch_derivatives_snapshot(self, inst_id: str, period: str = "1H") -> Optional[Dict]:
        """Снимок из 4 нативных публичных эндпоинтов OKX (без API-ключа)."""
        funding = self._get_funding_rate(inst_id)
        oi = self._get_open_interest(inst_id)
        taker = self._get_taker_volume_contract(inst_id, period)
        ccy = inst_id.split("-")[0]
        ls_ratio = self._get_long_short_ratio(ccy, period)

        if not funding and not oi and not taker:
            logger.warning(f"[OKX] Нет данных для {inst_id}, пропуск")
            return None

        ts = None
        for src in (taker, ls_ratio, funding, oi):
            if src and src.get("timestamp"):
                ts = src["timestamp"]
                break
        if not ts:
            return None

        return {
            "timestamp": ts,
            "funding_rate": funding.get("rate") if funding else None,
            "open_interest_contracts": oi.get("oi") if oi else None,
            "open_interest_usd": oi.get("oi_usd") if oi else None,
            "long_short_ratio": ls_ratio.get("ratio") if ls_ratio else None,
            "taker_buy_volume": taker.get("buy_volume") if taker else None,
            "taker_sell_volume": taker.get("sell_volume") if taker else None,
            "volume_usd": None,
        }

    def _get_funding_rate(self, inst_id: str) -> Optional[Dict]:
        try:
            r = requests.get(f"{self.BASE_URL}/public/funding-rate", params={"instId": inst_id}, timeout=10)
            r.raise_for_status()
            data = r.json().get("data") or []
            if not data:
                return None
            row = data[0]
            return {"timestamp": int(row["fundingTime"]),
                    "rate": float(row["fundingRate"]) if row.get("fundingRate") else None}
        except Exception as e:
            logger.error(f"[OKX] funding-rate {inst_id}: {e}")
            return None

    def _get_open_interest(self, inst_id: str) -> Optional[Dict]:
        try:
            r = requests.get(f"{self.BASE_URL}/public/open-interest",
                             params={"instType": "SWAP", "instId": inst_id}, timeout=10)
            r.raise_for_status()
            data = r.json().get("data") or []
            if not data:
                return None
            row = data[0]
            return {"timestamp": int(row["ts"]),
                    "oi": float(row["oi"]) if row.get("oi") else None,
                    "oi_usd": float(row["oiUsd"]) if row.get("oiUsd") else None}
        except Exception as e:
            logger.error(f"[OKX] open-interest {inst_id}: {e}")
            return None

    def _get_taker_volume_contract(self, inst_id: str, period: str) -> Optional[Dict]:
        try:
            r = requests.get(f"{self.BASE_URL}/rubik/stat/taker-volume-contract",
                             params={"instId": inst_id, "period": period}, timeout=10)
            r.raise_for_status()
            data = r.json().get("data") or []
            if not data:
                return None
            row = data[0]
            return {"timestamp": int(row[0]),
                    "sell_volume": float(row[1]) if len(row) > 1 else None,
                    "buy_volume": float(row[2]) if len(row) > 2 else None}
        except Exception as e:
            logger.error(f"[OKX] taker-volume-contract {inst_id}: {e}")
            return None

    def _get_long_short_ratio(self, ccy: str, period: str) -> Optional[Dict]:
        try:
            r = requests.get(f"{self.BASE_URL}/rubik/stat/contracts/long-short-account-ratio",
                             params={"ccy": ccy, "period": period}, timeout=10)
            r.raise_for_status()
            data = r.json().get("data") or []
            if not data:
                return None
            row = data[0]
            return {"timestamp": int(row[0]),
                    "ratio": float(row[1]) if len(row) > 1 else None}
        except Exception as e:
            logger.error(f"[OKX] long-short-account-ratio {ccy}: {e}")
            return None

    def fetch_liquidations(self, inst_id: str, uly: str = None, limit: int = 100) -> List[Dict]:
        """GET /api/v5/public/liquidation-orders — historical liquidations."""
        if uly is None:
            uly = inst_id.replace("-SWAP", "")
        try:
            r = requests.get(
                f"{self.BASE_URL}/public/liquidation-orders",
                params={"instType": "SWAP", "uly": uly, "state": "filled",
                        "instId": inst_id, "limit": str(min(limit, 100))},
                timeout=10,
            )
            r.raise_for_status()
            data = r.json().get("data") or []
            out = []
            for group in data:
                for d in group.get("details") or []:
                    out.append({
                        "timestamp": int(d["ts"]),
                        "pos_side": d.get("posSide", "").lower(),
                        "price": float(d["bkPx"]),
                        "size_contracts": float(d["sz"]),
                        "size_usd": float(d["bkPx"]) * float(d["sz"]),
                    })
            return out
        except Exception as e:
            logger.error(f"[OKX] liquidation-orders {inst_id}: {e}")
            return []

    def fetch_funding_history(self, inst_id: str, limit: int = 100) -> List[Dict]:
        try:
            r = requests.get(f"{self.BASE_URL}/public/funding-rate-history",
                             params={"instId": inst_id, "limit": str(min(limit, 100))}, timeout=10)
            r.raise_for_status()
            data = r.json().get("data") or []
            return [{"funding_time": int(row["fundingTime"]),
                     "realized_rate": float(row["realizedRate"])}
                    for row in data]
        except Exception as e:
            logger.error(f"[OKX] funding-history {inst_id}: {e}")
            return []
