# telegram_sender.py
import requests
import logging
from typing import Dict
from config import config
from datetime import datetime

logger = logging.getLogger(__name__)


class TelegramSender:
    def __init__(self):
        self.bot_token = config.TELEGRAM_BOT_TOKEN
        self.channel_id = config.TELEGRAM_CHANNEL_ID
        self.base_url = f"https://api.telegram.org/bot{self.bot_token}"

    def format_message(self, data: Dict) -> str:
        """Форматирование сообщения для отправки в Telegram."""
        signal = data.get('overall_signal', 'NEUTRAL')
        signal_emoji = {
            'STRONG BUY': '🚀',
            'BUY': '📈',
            'NEUTRAL': '⚪️',
            'SELL': '📉',
            'STRONG SELL': '🔻',
        }.get(signal, '⚪️')

        score = data.get('overall_score', 0)
        symbol = data.get('symbol', 'UNKNOWN').upper()
        source = data.get('source', config.DATA_SOURCE).upper()

        message = f"""
*{symbol} Анализ Осцилляторов* ({source})
⏰ *{datetime.now().strftime('%Y-%m-%d %H:%M UTC')}*

*Текущая цена:* ${data.get('current_price', 'N/A')}

{signal_emoji} *Общий сигнал: {signal}*
*Общий скорр балл:* {score}/14

━━━━━━━━━━━━━━━━━
*Детальный анализ осцилляторов:*

1️⃣ *RSI (14):* {data.get('rsi', 'N/A')}
   Сигнал: {self._format_signal(data.get('rsi_signal'))}

2️⃣ *MACD:* {data.get('macd', 'N/A')}
   Сигнальная линия: {data.get('macd_signal_line', 'N/A')}
   Гистограмма: {data.get('macd_histogram', 'N/A')}
   Сигнал: {self._format_signal(data.get('macd_signal'))}

3️⃣ *Stochastic:* %K: {data.get('stoch_k', 'N/A')} %D: {data.get('stoch_d', 'N/A')}
   Сигнал: {self._format_signal(data.get('stoch_signal'))}

4️⃣ *CCI (20):* {data.get('cci', 'N/A')}
   Сигнал: {self._format_signal(data.get('cci_signal'))}

5️⃣ *Williams %R (14):* {data.get('williams_r', 'N/A')}
   Сигнал: {self._format_signal(data.get('williams_r_signal'))}

6️⃣ *MFI (14):* {data.get('mfi', 'N/A')}
   Сигнал: {self._format_signal(data.get('mfi_signal'))}

7️⃣ *Ultimate Oscillator:* {data.get('ultimate_oscillator', 'N/A')}
   Сигнал: {self._format_signal(data.get('uo_signal'))}

8️⃣ *ATR (14):* {data.get('atr', 'N/A')}

9️⃣ *Bollinger Bands (20,2):*
   Верхняя: {data.get('bb_upper', 'N/A')}
   Средняя: {data.get('bb_middle', 'N/A')}
   Нижняя: {data.get('bb_lower', 'N/A')}
   Позиция: {self._format_signal(data.get('bb_position'))}

━━━━━━━━━━━━━━━━━
*Детализация скора:*
{chr(10).join(f"• {detail}" for detail in data.get('score_details', []))}

⚠️ *Дисклеймер:* Данный анализ носит информационный характер и не является инвестиционной рекомендацией.
"""
        return message

    def _format_signal(self, signal: str) -> str:
        """Форматирование сигнала с эмодзи."""
        if not signal:
            return "Нет данных"
        signals = {
            'oversold': '🟢 Перепродан',
            'overbought': '🔴 Перекуплен',
            'bullish': '🟢 Бычий',
            'bearish': '🔴 Медвежий',
            'neutral': '⚪️ Нейтральный',
            'below_lower': '🟢 Ниже нижней полосы',
            'above_upper': '🔴 Выше верхней полосы',
            'between': '⚪️ В пределах полос',
            'no_data': '⚠️ Недостаточно данных',
        }
        return signals.get(signal, signal)

    def send_message(self, data: Dict) -> bool:
        """Отправка сообщения в Telegram канал."""
        if not self.bot_token or not self.channel_id:
            logger.warning("Telegram не настроен. Пропускаем отправку.")
            return False

        try:
            message = self.format_message(data)
            url = f"{self.base_url}/sendMessage"
            payload = {
                'chat_id': self.channel_id,
                'text': message,
                'parse_mode': 'Markdown',
                'disable_web_page_preview': True,
            }
            response = requests.post(url, json=payload)
            response.raise_for_status()
            result = response.json()

            if result.get('ok'):
                logger.info("Сообщение успешно отправлено в Telegram")
                return True
            else:
                logger.error(f"Ошибка при отправке в Telegram: {result}")
                return False
        except Exception as e:
            logger.error(f"Ошибка при отправке сообщения в Telegram: {e}")
            return False


telegram_sender = TelegramSender()