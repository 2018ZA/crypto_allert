import requests
import logging
from datetime import datetime
from typing import List, Dict
from config import config

logger = logging.getLogger(__name__)

class BinanceClient:
    def __init__(self):
        self.base_url = config.BINANCE_API_URL
        self.symbol = config.SYMBOL
        self.interval = config.INTERVAL
    
    def fetch_klines(self, limit: int = 100) -> List[Dict]:
        """
        Получение данных свечей с Binance
        
        Returns:
            List[Dict]: Список свечей с полями:
                - open_time: время открытия
                - open: цена открытия
                - high: максимальная цена
                - low: минимальная цена
                - close: цена закрытия
                - volume: объем
                - close_time: время закрытия
                - quote_volume: объем в котировочной валюте
                - trades: количество сделок
        """
        try:
            params = {
                'symbol': self.symbol,
                'interval': self.interval,
                'limit': limit
            }
            
            response = requests.get(self.base_url, params=params)
            response.raise_for_status()
            
            data = response.json()
            
            klines = []
            for k in data:
                klines.append({
                    'open_time': k[0],
                    'open': k[1],
                    'high': k[2],
                    'low': k[3],
                    'close': k[4],
                    'volume': k[5],
                    'close_time': k[6],
                    'quote_volume': k[7],
                    'trades': k[8]
                })
            
            logger.info(f"Получено {len(klines)} свечей с Binance")
            return klines
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Ошибка при запросе к Binance API: {e}")
            raise
        except (KeyError, IndexError) as e:
            logger.error(f"Ошибка при парсинге данных: {e}")
            raise

binance_client = BinanceClient()