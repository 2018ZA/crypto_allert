# main.py
import schedule
import time
import logging
from datetime import datetime
import sys



from config import config
from database import db
from clients.factory import get_client
from oscillators import oscillator_analyzer
from telegram_sender import telegram_sender

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('crypto_analyzer.log'),
        logging.StreamHandler(sys.stdout),
    ],
)
logger = logging.getLogger(__name__)


class CryptoAnalyzerApp:
    def __init__(self):
        self.is_running = False
        self.client = get_client(config.DATA_SOURCE)
        logger.info(f"Источник данных: {self.client.name}")

    def initialize(self):
        """Инициализация приложения."""
        logger.info("=" * 50)
        logger.info("Инициализация Crypto Analyzer")
        logger.info("=" * 50)

        db.create_tables()
        logger.info("База данных инициализирована")

        if not config.TELEGRAM_BOT_TOKEN or not config.TELEGRAM_CHANNEL_ID:
            logger.warning("Telegram не настроен! Сообщения не будут отправляться.")
            logger.warning(
                "Добавьте TELEGRAM_BOT_TOKEN и TELEGRAM_CHANNEL_ID в .env файл"
            )

        logger.info("Инициализация завершена успешно")

    def _filter_oscillator_fields(self, analysis_result: dict) -> dict:
        """Фильтрация полей для сохранения в OscillatorData."""
        allowed_fields = [
            'rsi', 'rsi_signal',
            'macd', 'macd_signal_line', 'macd_histogram', 'macd_signal',
            'stoch_k', 'stoch_d', 'stoch_signal',
            'cci', 'cci_signal',
            'williams_r', 'williams_r_signal',
            'mfi', 'mfi_signal',
            'ultimate_oscillator', 'uo_signal',
            'atr',
            'bb_upper', 'bb_middle', 'bb_lower', 'bb_position',
            'overall_score', 'overall_signal',
        ]
        filtered = {k: analysis_result[k] for k in allowed_fields if k in analysis_result}
        filtered['timestamp'] = analysis_result.get('timestamp', datetime.now())
        filtered['symbol'] = analysis_result.get('symbol', 'unknown')
        return filtered

    def get_latest_kline(self, symbol: str):
        """Получение последней свечи из БД для указанного инструмента."""
        try:
            with db.get_session() as session:
                from models import KlineData
                from sqlalchemy import desc

                latest = (
                    session.query(KlineData)
                    .filter_by(symbol=symbol)
                    .order_by(desc(KlineData.open_time))
                    .first()
                )
                if latest:
                    return {
                        'id': latest.id,
                        'open_time': latest.open_time,
                        'close_price': latest.close_price,
                    }
                return None
        except Exception as e:
            logger.error(f"Ошибка при получении последней свечи {symbol}: {e}")
            return None

    def process_update(self):
        """Основная логика обновления для всех инструментов."""
        try:
            logger.info("-" * 50)
            logger.info(f"Запуск обновления: {datetime.now()}")

            if not self.client.is_available():
                logger.error(f"{self.client.name} недоступен, пропуск итерации")
                return

            for instrument in config.INSTRUMENTS:
                inst_id = instrument["id"]
                symbol = config.symbol_for(instrument)

                if symbol is None:
                    logger.debug(
                        f"[{inst_id}] недоступен на {self.client.name}, пропуск"
                    )
                    continue

                logger.info(f"--- Обработка {inst_id} ({symbol}) ---")

                # Определяем, сколько свечей запрашивать
                latest_kline = self.get_latest_kline(inst_id)
                if latest_kline:
                    time_since_last = datetime.now() - latest_kline['open_time']
                    hours_since_last = time_since_last.total_seconds() / 3600
                    logger.info(
                        f"[{inst_id}] Последняя свеча: {latest_kline['open_time']}, "
                        f"прошло часов: {hours_since_last:.2f}"
                    )
                    if hours_since_last < 0.92:
                        logger.info(
                            f"[{inst_id}] Данные актуальны (< 55 мин), пропуск"
                        )
                        continue
                    limit = max(1, min(int(hours_since_last), config.LIMIT))
                else:
                    logger.info(f"[{inst_id}] Нет данных в БД. Первичная загрузка...")
                    limit = config.LIMIT

                # 1. Получаем свечи
                klines = self.client.fetch_candles(
                    symbol, config.INTERVAL, limit
                )
                if not klines:
                    logger.warning(
                        f"[{inst_id}] Не удалось получить свечи, пропуск"
                    )
                    continue

                # 2. Сохраняем в БД
                db.save_kline_data(klines, symbol=inst_id)

                # 3. Читаем последние 100 свечей из БД
                klines_from_db = db.get_last_klines(inst_id, limit=100)
                if len(klines_from_db) < 28:
                    logger.warning(
                        f"[{inst_id}] Недостаточно данных для анализа: "
                        f"{len(klines_from_db)} свечей (нужно минимум 28)"
                    )
                    continue

                # 4. Рассчитываем осцилляторы
                analysis_result = oscillator_analyzer.analyze_all(klines_from_db)
                analysis_result['symbol'] = inst_id
                analysis_result['source'] = self.client.name

                # 5. Сохраняем осцилляторы
                latest_kline_id = db.get_latest_kline_id(inst_id)
                oscillator_fields = self._filter_oscillator_fields(analysis_result)
                db.save_oscillator_data(oscillator_fields, latest_kline_id)

                # 6. Отправляем в Telegram
                telegram_sender.send_message(analysis_result)

                logger.info(
                    f"[{inst_id}] Анализ завершён: "
                    f"{analysis_result['overall_signal']} "
                    f"({analysis_result['overall_score']}/14)"
                )

        except Exception as e:
            logger.error(f"Критическая ошибка при обновлении: {e}", exc_info=True)

    def run_once(self):
        """Запуск одного цикла обновления."""
        logger.info("Запуск однократного обновления")
        self.process_update()

    def start_scheduler(self):
        """Запуск планировщика."""
        self.initialize()
        logger.info("Выполнение первого обновления...")
        self.process_update()

        schedule.every(config.UPDATE_INTERVAL_HOURS).hours.do(self.process_update)
        logger.info(
            f"Планировщик запущен. Обновление каждые "
            f"{config.UPDATE_INTERVAL_HOURS} час(а)"
        )

        self.is_running = True
        try:
            while self.is_running:
                schedule.run_pending()
                time.sleep(1)
        except KeyboardInterrupt:
            logger.info("Приложение остановлено пользователем")
            self.is_running = False

    def sync_derivatives(self):
        """Синхронизация деривативных метрик для инструментов OKX."""
        if not config.DERIVATIVES_ENABLED:
            return
        if self.client.name != "okx":
            logger.debug("Деривативы поддерживаются только для OKX, пропуск")
            return

        for instrument in config.INSTRUMENTS:
            inst_id = instrument.get("okx")
            if not inst_id:
                continue
            # Для деривативов используем SWAP-версию, даже если в конфиге спот
            if not inst_id.endswith("-SWAP"):
                inst_id = inst_id + "-SWAP"

            symbol = instrument["id"]

            # 1) Снимок текущих метрик
            snapshot = self.client.fetch_derivatives_snapshot(
                inst_id, period=config.DERIVATIVES_PERIOD
            )
            if snapshot:
                db.save_derivatives_snapshot(symbol, inst_id, snapshot)

            # 2) История funding (раз в сутки или при первом запуске)
            #    Можно вызывать не каждый цикл, а по расписанию
            # events = self.client.fetch_funding_history(inst_id, limit=config.FUNDING_HISTORY_LIMIT)
            # if events:
            #     db.save_funding_events(symbol, inst_id, events)

        logger.info("Синхронизация деривативов завершена")


def main():
    app = CryptoAnalyzerApp()

    if len(sys.argv) > 1:
        if sys.argv[1] == '--once':
            app.initialize()
            app.run_once()

        elif sys.argv[1] == '--test':
            app.initialize()
            logger.info("Тестовый запуск...")
            try:
                for instrument in config.INSTRUMENTS:
                    inst_id = instrument["id"]
                    symbol = config.symbol_for(instrument)
                    if symbol is None:
                        continue

                    logger.info(f"--- Тест {inst_id} ({symbol}) ---")
                    latest_kline = app.get_latest_kline(inst_id)
                    if latest_kline:
                        time_diff = datetime.now() - latest_kline['open_time']
                        hours_since_last = time_diff.total_seconds() / 3600
                        if hours_since_last < 0.92:
                            limit = 1
                        else:
                            limit = max(1, min(int(hours_since_last), config.LIMIT))
                    else:
                        limit = config.LIMIT

                    klines = app.client.fetch_candles(symbol, config.INTERVAL, limit)
                    logger.info(f"[{inst_id}] Получено {len(klines)} свечей с API")
                    db.save_kline_data(klines, symbol=inst_id)

                    klines_from_db = db.get_last_klines(inst_id, 100)
                    logger.info(
                        f"[{inst_id}] Получено {len(klines_from_db)} свечей из БД"
                    )

                    if len(klines_from_db) < 28:
                        logger.warning(
                            f"[{inst_id}] Недостаточно данных для анализа"
                        )
                        continue

                    analysis_result = oscillator_analyzer.analyze_all(klines_from_db)
                    analysis_result['symbol'] = inst_id
                    latest_kline_id = db.get_latest_kline_id(inst_id)
                    oscillator_fields = app._filter_oscillator_fields(analysis_result)
                    db.save_oscillator_data(oscillator_fields, latest_kline_id)

                    print("\n" + "=" * 50)
                    print(f"РЕЗУЛЬТАТЫ АНАЛИЗА: {inst_id}")
                    print("=" * 50)
                    print(telegram_sender.format_message(analysis_result))

            except Exception as e:
                logger.error(f"Ошибка при тестовом запуске: {e}", exc_info=True)
                import traceback
                traceback.print_exc()

        else:
            print("Использование:")
            print("  python main.py          - запуск планировщика (каждый час)")
            print("  python main.py --once   - однократное выполнение")
            print("  python main.py --test   - тестовый запуск с выводом в консоль")
    else:
        app.start_scheduler()


if __name__ == "__main__":
    app = CryptoAnalyzerApp()
    app.initialize()

    # Основной цикл анализа (существующий)
    schedule.every(config.UPDATE_INTERVAL_HOURS).hours.do(app.process_update)

    # Синхронизация деривативов — отдельная задача, чаще
    if config.DERIVATIVES_ENABLED:
        schedule.every(config.DERIVATIVES_SYNC_INTERVAL_MIN).minutes.do(app.sync_derivatives)

    while True:
        schedule.run_pending()
        time.sleep(1)