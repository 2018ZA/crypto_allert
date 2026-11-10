# database.py
from sqlalchemy import create_engine, desc
from sqlalchemy.orm import sessionmaker, Session
from contextlib import contextmanager
from models import Base, KlineData, OscillatorData
from config import config
from datetime import datetime
from typing import List, Optional
import logging

logger = logging.getLogger(__name__)


class Database:
    def __init__(self):
        self.engine = create_engine(
            config.database_url,
            pool_size=10,
            max_overflow=20,
            pool_pre_ping=True,
        )
        self.SessionLocal = sessionmaker(bind=self.engine)

    def create_tables(self):
        """Создание всех таблиц в базе данных."""
        try:
            Base.metadata.create_all(self.engine)
            logger.info("Таблицы успешно созданы")
        except Exception as e:
            logger.error(f"Ошибка при создании таблиц: {e}")
            raise

    @contextmanager
    def get_session(self) -> Session:
        """Контекстный менеджер для работы с сессией."""
        session = self.SessionLocal()
        try:
            yield session
            session.commit()
        except Exception as e:
            session.rollback()
            logger.error(f"Ошибка при работе с базой данных: {e}")
            raise
        finally:
            session.close()

    def save_kline_data(self, kline_list: List[dict], symbol: str):
        """
        Сохранение данных свечей в БД для указанного инструмента.
        :param kline_list: список свечей в едином формате
        :param symbol: внутренний ID инструмента (например, 'btc')
        """
        with self.get_session() as session:
            saved_count = 0
            for kline in kline_list:
                try:
                    existing = session.query(KlineData).filter_by(
                        open_time=datetime.fromtimestamp(kline['open_time'] / 1000),
                        symbol=symbol,
                    ).first()

                    if not existing:
                        kline_data = KlineData(
                            symbol=symbol,
                            open_time=datetime.fromtimestamp(kline['open_time'] / 1000),
                            close_time=datetime.fromtimestamp(kline['close_time'] / 1000),
                            open_price=float(kline['open']),
                            high_price=float(kline['high']),
                            low_price=float(kline['low']),
                            close_price=float(kline['close']),
                            volume=float(kline['volume']),
                            quote_volume=float(kline['quote_volume']),
                            trades_count=int(kline.get('trades', 0)),
                        )
                        session.add(kline_data)
                        saved_count += 1
                        logger.info(f"Сохранена свеча {symbol} за {kline_data.open_time}")
                except Exception as e:
                    logger.error(
                        f"Ошибка при сохранении свечи {symbol}: {e}, "
                        f"данные: {kline.keys()}"
                    )
                    continue
            logger.info(f"Всего сохранено {saved_count} новых свечей для {symbol}")

    def save_oscillator_data(self, osc_data: dict, kline_id: int):
        """Сохранение данных осцилляторов."""
        with self.get_session() as session:
            oscillator = OscillatorData(**osc_data, kline_id=kline_id)
            session.add(oscillator)
            logger.info(f"Сохранены данные осцилляторов для свечи {kline_id}")

    def get_last_klines(self, symbol: str, limit: int = 100) -> List[dict]:
        """Получение последних свечей для указанного инструмента."""
        with self.get_session() as session:
            klines = (
                session.query(KlineData)
                .filter_by(symbol=symbol)
                .order_by(desc(KlineData.open_time))
                .limit(limit)
                .all()
            )
            return [
                {
                    'open_time': k.open_time,
                    'open': k.open_price,
                    'high': k.high_price,
                    'low': k.low_price,
                    'close': k.close_price,
                    'volume': k.volume,
                }
                for k in reversed(klines)
            ]

    def get_latest_kline_id(self, symbol: str) -> Optional[int]:
        """Получение ID последней сохранённой свечи для инструмента."""
        with self.get_session() as session:
            latest = (
                session.query(KlineData)
                .filter_by(symbol=symbol)
                .order_by(desc(KlineData.open_time))
                .first()
            )
            return latest.id if latest else None


db = Database()