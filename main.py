import schedule
import time
import logging
from datetime import datetime
import sys

from config import config
from database import db
from binance_client import binance_client
from oscillators import oscillator_analyzer
from telegram_sender import telegram_sender

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('crypto_analyzer.log'),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)

class CryptoAnalyzerApp:
    def __init__(self):
        self.is_running = False
        
    def initialize(self):
        """Инициализация приложения"""
        logger.info("=" * 50)
        logger.info("Инициализация Crypto Analyzer")
        logger.info("=" * 50)
        
        db.create_tables()
        logger.info("База данных инициализирована")
        
        if not config.TELEGRAM_BOT_TOKEN or not config.TELEGRAM_CHANNEL_ID:
            logger.warning("Telegram не настроен! Сообщения не будут отправляться.")
            logger.warning("Добавьте TELEGRAM_BOT_TOKEN и TELEGRAM_CHANNEL_ID в .env файл")
        
        logger.info("Инициализация завершена успешно")
    
    def _filter_oscillator_fields(self, analysis_result):
        """Фильтрация полей для сохранения в OscillatorData"""
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
            'overall_score', 'overall_signal'
        ]
        
        filtered = {}
        for field in allowed_fields:
            if field in analysis_result:
                filtered[field] = analysis_result[field]
        
        filtered['timestamp'] = analysis_result.get('timestamp', datetime.now())
        filtered['symbol'] = analysis_result.get('symbol', config.SYMBOL)
        
        return filtered
    
    def get_latest_kline(self):
        """Получение последней свечи из БД (возвращает словарь)"""
        try:
            with db.get_session() as session:
                from models import KlineData
                from sqlalchemy import desc
                
                latest = session.query(KlineData)\
                    .filter_by(symbol=config.SYMBOL)\
                    .order_by(desc(KlineData.open_time))\
                    .first()
                
                if latest:
                    return {
                        'id': latest.id,
                        'open_time': latest.open_time,
                        'close_price': latest.close_price
                    }
                return None
        except Exception as e:
            logger.error(f"Ошибка при получении последней свечи: {e}")
            return None
    
    def process_update(self):
        """Основная логика обновления"""
        try:
            logger.info("-" * 50)
            logger.info(f"Запуск обновления: {datetime.now()}")
            
            latest_kline = self.get_latest_kline()
            
            if latest_kline:
                time_since_last = datetime.now() - latest_kline['open_time']
                hours_since_last = time_since_last.total_seconds() / 3600
                
                logger.info(f"Последняя свеча в БД: {latest_kline['open_time']}")
                logger.info(f"Прошло часов: {hours_since_last:.2f}")
                
                if hours_since_last < 0.92:
                    logger.info("Данные актуальны (прошло < 55 мин), пропускаем обновление")
                    return
                
                hours_missed = int(hours_since_last)
                limit = max(1, min(hours_missed, 100))
                
                logger.info(f"Пропущено часов: {hours_missed}")
                logger.info(f"Будет запрошено свечей: {limit}")
            else:
                logger.info("Нет данных в БД. Первичная загрузка...")
                limit = 100
            
            logger.info("Шаг 1: Получение данных с Binance API")
            klines = binance_client.fetch_klines(limit=limit)
            logger.info(f"Получено {len(klines)} свечей")
            
            logger.info("Шаг 2: Сохранение данных в базу данных")
            db.save_kline_data(klines)
            
            latest_kline_id = db.get_latest_kline_id()
            
            logger.info("Шаг 3: Расчет осцилляторов")
            klines_from_db = db.get_last_klines(100)
            
            if len(klines_from_db) < 28:
                logger.warning(f"Недостаточно данных для расчета: {len(klines_from_db)} свечей. Нужно минимум 28.")
                return
            
            analysis_result = oscillator_analyzer.analyze_all(klines_from_db)
            
            logger.info("Шаг 4: Сохранение данных осцилляторов")
            oscillator_fields = self._filter_oscillator_fields(analysis_result)
            db.save_oscillator_data(oscillator_fields, latest_kline_id)
            
            logger.info("Шаг 5: Отправка сообщения в Telegram")
            telegram_sender.send_message(analysis_result)
            
            logger.info("Обновление завершено успешно")
            logger.info(f"Общий сигнал: {analysis_result['overall_signal']}")
            logger.info(f"Общий скорр: {analysis_result['overall_score']}/14")
            
        except Exception as e:
            logger.error(f"Критическая ошибка при обновлении: {e}", exc_info=True)
    
    def run_once(self):
        """Запуск одного цикла обновления"""
        logger.info("Запуск однократного обновления")
        self.process_update()
    
    def start_scheduler(self):
        """Запуск планировщика"""
        self.initialize()
        
        logger.info("Выполнение первого обновления...")
        self.process_update()
        
        schedule.every(config.UPDATE_INTERVAL_HOURS).hours.do(self.process_update)
        
        logger.info(f"Планировщик запущен. Обновление каждые {config.UPDATE_INTERVAL_HOURS} час(а)")
        
        self.is_running = True
        
        try:
            while self.is_running:
                schedule.run_pending()
                time.sleep(1)
        except KeyboardInterrupt:
            logger.info("Приложение остановлено пользователем")
            self.is_running = False

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
                latest_kline = app.get_latest_kline()
                if latest_kline:
                    time_diff = datetime.now() - latest_kline['open_time']
                    hours_since_last = time_diff.total_seconds() / 3600
                    logger.info(f"Последняя свеча в БД: {latest_kline['open_time']}")
                    logger.info(f"Прошло часов: {hours_since_last:.2f}")
                    
                    if hours_since_last < 0.92:
                        limit = 1
                    else:
                        limit = max(1, min(int(hours_since_last), 100))
                else:
                    limit = 100
                
                logger.info(f"Запрошено свечей: {limit}")
                klines = binance_client.fetch_klines(limit=limit)
                logger.info(f"Получено {len(klines)} свечей с API")
                
                db.save_kline_data(klines)
                logger.info("Свечи сохранены в БД")
                
                latest_kline_id = db.get_latest_kline_id()
                klines_from_db = db.get_last_klines(100)
                logger.info(f"Получено {len(klines_from_db)} свечей из БД для анализа")
                
                if len(klines_from_db) < 28:
                    logger.warning(f"Недостаточно данных для расчета осцилляторов. Нужно 28, есть {len(klines_from_db)}")
                    print(f"\n⚠️  Недостаточно данных. Нужно минимум 28 свечей, а получено {len(klines_from_db)}")
                    return
                
                analysis_result = oscillator_analyzer.analyze_all(klines_from_db)
                logger.info("Анализ осцилляторов выполнен")
                
                oscillator_fields = app._filter_oscillator_fields(analysis_result)
                db.save_oscillator_data(oscillator_fields, latest_kline_id)
                logger.info("Результаты осцилляторов сохранены в БД")
                
                print("\n" + "="*50)
                print("РЕЗУЛЬТАТЫ АНАЛИЗА")
                print("="*50)
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
    main()