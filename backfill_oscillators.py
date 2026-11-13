#!/usr/bin/env python3
"""
Backfill oscillator_data для исторических свечей без осцилляторов.

Использование:
    venv/bin/python backfill_oscillators.py --dry-run           # показать план, ничего не писать
    venv/bin/python backfill_oscillators.py                     # выполнить
    venv/bin/python backfill_oscillators.py --symbol BTCUSDT    # только один символ
    venv/bin/python backfill_oscillators.py --limit 10          # только 10 свечей (тест)
"""
import argparse
import logging
import sys

from database import db
from models import KlineData, OscillatorData
from sqlalchemy import select
from oscillators import oscillator_analyzer
from main import CryptoAnalyzerApp

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s: %(message)s")
log = logging.getLogger(__name__)

WINDOW_SIZE = 100   # как в process_update
MIN_KLINES = 28     # минимум для анализа

_app = CryptoAnalyzerApp()


def kline_to_dict(k):
    return {
        'open_time': k.open_time, 'open': k.open_price, 'high': k.high_price,
        'low': k.low_price, 'close': k.close_price, 'volume': k.volume,
    }


def get_window(session, symbol, target_time, size=WINDOW_SIZE):
    rows = session.execute(
        select(KlineData)
        .where(KlineData.symbol == symbol)
        .where(KlineData.open_time <= target_time)
        .order_by(KlineData.open_time.desc())
        .limit(size)
    ).scalars().all()
    return list(reversed(rows))


def process_one(session, kline, dry_run=False):
    exists_id = session.execute(
        select(OscillatorData.id).where(OscillatorData.kline_id == kline.id).limit(1)
    ).scalar_one_or_none()
    if exists_id:
        return "skip_exists", None, None

    window = get_window(session, kline.symbol, kline.open_time)
    if len(window) < MIN_KLINES:
        return "skip_short", None, None

    dicts = [kline_to_dict(k) for k in window]
    result = oscillator_analyzer.analyze_all(dicts)
    result['symbol'] = kline.symbol

    if dry_run:
        return "would_save", result['overall_score'], result['overall_signal']

    osc_fields = _app._filter_oscillator_fields(result)
    db.save_oscillator_data(osc_fields, kline.id)
    return "saved", result['overall_score'], result['overall_signal']


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--dry-run', action='store_true')
    parser.add_argument('--symbol', type=str, default=None)
    parser.add_argument('--limit', type=int, default=None)
    parser.add_argument('--batch', type=int, default=200)
    args = parser.parse_args()

    log.info(f"BACKFILL START | dry_run={args.dry_run} symbol={args.symbol} limit={args.limit}")

    with db.get_session() as session:
        q = (
            select(KlineData)
            .outerjoin(OscillatorData, KlineData.id == OscillatorData.kline_id)
            .where(OscillatorData.id.is_(None))
            .order_by(KlineData.symbol, KlineData.open_time)
        )
        if args.symbol:
            q = q.where(KlineData.symbol == args.symbol)
        if args.limit:
            q = q.limit(args.limit)

        klines = session.execute(q).scalars().all()
        log.info(f"Кандидатов: {len(klines)}")

        stats = {'saved': 0, 'would_save': 0, 'skip_short': 0, 'skip_exists': 0, 'errors': 0}

        for i, kline in enumerate(klines, 1):
            try:
                status, score, signal = process_one(session, kline, dry_run=args.dry_run)
                stats[status] += 1
                if i % args.batch == 0 or i == len(klines):
                    log.info(f"Progress {i}/{len(klines)} | {stats}")
                if status in ('saved', 'would_save') and args.limit and args.limit <= 20:
                    log.info(f"  [{kline.symbol}] {kline.open_time}: score={score} signal={signal}")
            except Exception as e:
                stats['errors'] += 1
                log.error(f"Error on {kline.symbol} {kline.open_time}: {e}")

        log.info(f"BACKFILL DONE | {stats}")


if __name__ == "__main__":
    main()
