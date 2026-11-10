# config.py
import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # --- База данных ---
    DB_HOST = os.getenv('DB_HOST', 'localhost')
    DB_PORT = os.getenv('DB_PORT', '5432')
    DB_NAME = os.getenv('DB_NAME', 'crypto_analyzer')
    DB_USER = os.getenv('DB_USER', 'postgres')
    DB_PASSWORD = os.getenv('DB_PASSWORD', '')

    # --- Telegram ---
    TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN', '')
    TELEGRAM_CHANNEL_ID = os.getenv('TELEGRAM_CHANNEL_ID', '')

    # --- Источник данных ---
    # Допустимые значения: "okx" | "binance"
    DATA_SOURCE = os.getenv('DATA_SOURCE', 'okx').lower()

    # Таймфрейм в едином формате (маппинг внутри клиентов)
    INTERVAL = os.getenv('INTERVAL', '1H')   # "1m", "5m", "1H", "4H", "1D" и т.д.
    LIMIT = 100                               # Сколько свечей запрашивать

    # --- Реестр инструментов ---
    # Для каждого источника указан свой тикер.
    # None означает, что инструмент недоступен на этом источнике.
    INSTRUMENTS = [
    {"id": "BTCUSDT",  "okx": "BTC-USDT",  "okx_type": "SPOT", "binance": "BTCUSDT"},
    {"id": "ETHUSDT",  "okx": "ETH-USDT",  "okx_type": "SPOT", "binance": "ETHUSDT"},
    {"id": "BNBUSDT",  "okx": "BNB-USDT",  "okx_type": "SPOT", "binance": "BNBUSDT"},
    {"id": "XRPUSDT",  "okx": "XRP-USDT",  "okx_type": "SPOT", "binance": "XRPUSDT"},
    {"id": "SOLUSDT",  "okx": "SOL-USDT",  "okx_type": "SPOT", "binance": "SOLUSDT"},
    {"id": "TRXUSDT",  "okx": "TRX-USDT",  "okx_type": "SPOT", "binance": "TRXUSDT"},
    {"id": "DOGEUSDT", "okx": "DOGE-USDT", "okx_type": "SPOT", "binance": "DOGEUSDT"},
    {"id": "ADAUSDT",  "okx": "ADA-USDT",  "okx_type": "SPOT", "binance": "ADAUSDT"},
    {"id": "JUPUSDT",  "okx": "JUP-USDT",  "okx_type": "SPOT", "binance": "JUPUSDT"},
    {"id": "LINKUSDT", "okx": "LINK-USDT", "okx_type": "SPOT", "binance": "LINKUSDT"},
    {"id": "XAUUSDT",  "okx": "XAU-USDT-SWAP", "okx_type": "SWAP", "binance": None},
    {"id": "XAGUSDT",  "okx": "XAG-USDT-SWAP", "okx_type": "SWAP", "binance": None},
    {"id": "XPTUSDT",  "okx": "XPT-USDT-SWAP", "okx_type": "SWAP", "binance": None},
]

    UPDATE_INTERVAL_HOURS = int(os.getenv('UPDATE_INTERVAL_HOURS', '1'))

    @property
    def database_url(self) -> str:
        return (
            f"postgresql://{self.DB_USER}:{self.DB_PASSWORD}"
            f"@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"
        )

    @classmethod
    def symbol_for(cls, instrument: dict):
        """Возвращает тикер для активного источника или None."""
        return instrument.get(cls.DATA_SOURCE)


config = Config()