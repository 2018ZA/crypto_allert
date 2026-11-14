#!/usr/bin/env python3
"""One-time loader: fetch historical 1h candles from OKX for each symbol.

Paginates GET /api/v5/market/history-candles using `after` cursor.
Saves to kline_data via db.save_kline_data (upsert-safe).
"""
import argparse
import logging
import time
from datetime import datetime, timezone
from typing import Optional

import requests

from config import config
from database import db
from models import KlineData
from sqlalchemy import select, func

logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s: %(message)s')
log = logging.getLogger(__name__)

OKX_BASE = "https://www.okx.com/api/v5"


def to_swap(okx: str) -> str:
    return okx if okx.endswith("-SWAP") else okx + "-SWAP"


def fetch_page(inst_id: str, after_ms: Optional[int] = None, limit: int = 100) -> list:
    """Fetch one page of history-candles. Returns raw OKX rows."""
    params = {"instId": inst_id, "bar": "1H", "limit": str(min(limit, 100))}
    if after_ms is not None:
        params["after"] = str(after_ms)
    r = requests.get(f"{OKX_BASE}/market/history-candles", params=params, timeout=15)
    r.raise_for_status()
    j = r.json()
    if j.get("code") != "0":
        raise RuntimeError(f"OKX error: {j.get('code')} {j.get('msg')}")
    return j.get("data") or []


def parse_row(row: list) -> dict:
    """OKX row: [ts, o, h, l, c, vol, volCcy, volCcyQuote, confirm]."""
    ts_ms = int(row[0])
    open_time = int(row[0])
    close_time = int(row[0]) + 3600 * 1000 - 1
    return {
        'open_time': open_time,
        'close_time': close_time,
        'open': float(row[1]),
        'high': float(row[2]),
        'low': float(row[3]),
        'close': float(row[4]),
        'volume': float(row[5]),
        'quote_volume': float(row[7]) if len(row) > 7 else 0.0,
        'trades_count': 0,
    }


def load_symbol(symbol: str, okx: str, target_bars: int) -> int:
    inst_id = to_swap(okx)
    log.info(f"[{symbol}] target={target_bars} bars from {inst_id}")
    saved_total = 0
    after_ms = None
    while saved_total < target_bars:
        try:
            rows = fetch_page(inst_id, after_ms=after_ms, limit=100)
        except Exception as e:
            log.error(f"[{symbol}] page fetch failed: {e}")
            break
        if not rows:
            log.info(f"[{symbol}] no more history (empty page)")
            break

        # OKX returns rows sorted DESC by timestamp. Our oldest = rows[-1].
        parsed = [parse_row(r) for r in rows]
        # Deduplicate by open_time within page
        seen = set()
        unique = []
        for p in parsed:
            if p['open_time'] not in seen:
                seen.add(p['open_time'])
                unique.append(p)
        # save_kline_data expects list; our method skips duplicates at DB level? Safe: relies on caller
        with db.get_session() as _s:
            _before = _s.execute(
                select(func.count()).select_from(KlineData).where(KlineData.symbol == symbol)
            ).scalar() or 0
        db.save_kline_data(unique, symbol=symbol)
        with db.get_session() as _s:
            _after = _s.execute(
                select(func.count()).select_from(KlineData).where(KlineData.symbol == symbol)
            ).scalar() or 0
        actual_saved = _after - _before
        saved_total += actual_saved

        oldest_ms = int(rows[-1][0])
        if after_ms is not None and oldest_ms >= after_ms:
            log.info(f"[{symbol}] cursor stuck, breaking")
            break
        after_ms = oldest_ms
        log.info(f"[{symbol}] page OK (saved={actual_saved}, total_saved={saved_total}, oldest_ms={oldest_ms})")

        if saved_total >= target_bars:
            break
        time.sleep(0.15)  # politeness / rate limit

    log.info(f"[{symbol}] DONE, {saved_total} bars considered")
    return saved_total


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--bars', type=int, default=2000, help='target bars per symbol')
    ap.add_argument('--symbols', nargs='*', default=None, help='optional symbol subset')
    args = ap.parse_args()

    db.create_tables()

    total = 0
    for inst in config.INSTRUMENTS:
        sym = inst['id']
        okx = inst.get('okx')
        if not okx:
            continue
        if args.symbols and sym not in args.symbols:
            continue
        try:
            n = load_symbol(sym, okx, args.bars)
            total += n
        except Exception as e:
            log.exception(f"[{sym}] FAILED: {e}")

    log.info(f"ALL DONE, total bars considered: {total}")


if __name__ == '__main__':
    main()
