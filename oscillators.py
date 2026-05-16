import numpy as np
import pandas as pd
from typing import Dict, List, Tuple
import logging

logger = logging.getLogger(__name__)

class OscillatorAnalyzer:
    def __init__(self):
        self.rsi_period = 14
        self.stoch_period = 14
        self.macd_fast = 12
        self.macd_slow = 26
        self.macd_signal = 9
        self.cci_period = 20
        self.williams_period = 14
        self.mfi_period = 14
        self.atr_period = 14
        self.bb_period = 20
        
    def calculate_rsi(self, closes: List[float]) -> Tuple[float, str]:
        """
        Расчет RSI (Relative Strength Index)
        Выше 70 - перекуплен, ниже 30 - перепродан
        """
        if len(closes) < self.rsi_period + 1:
            return None, "no_data"
            
        deltas = np.diff(closes)
        gains = np.where(deltas > 0, deltas, 0)
        losses = np.where(deltas < 0, -deltas, 0)
        
        avg_gain = np.mean(gains[-self.rsi_period:])
        avg_loss = np.mean(losses[-self.rsi_period:])
        
        if avg_loss == 0:
            rsi = 100
        else:
            rs = avg_gain / avg_loss
            rsi = 100 - (100 / (1 + rs))
        
        if rsi >= 70:
            signal = "overbought"
        elif rsi <= 30:
            signal = "oversold"
        else:
            signal = "neutral"
            
        return round(rsi, 2), signal
    
    def calculate_macd(self, closes: List[float]) -> Tuple[float, float, float, str]:
        """
        Расчет MACD
        MACD > Signal Line - бычий сигнал
        MACD < Signal Line - медвежий сигнал
        """
        if len(closes) < self.macd_slow + self.macd_signal:
            return None, None, None, "no_data"
        
        closes_series = pd.Series(closes)
        
        ema_fast = closes_series.ewm(span=self.macd_fast, adjust=False).mean()
        ema_slow = closes_series.ewm(span=self.macd_slow, adjust=False).mean()
        
        macd_line = ema_fast - ema_slow
        signal_line = macd_line.ewm(span=self.macd_signal, adjust=False).mean()
        histogram = macd_line - signal_line
        
        current_macd = macd_line.iloc[-1]
        current_signal = signal_line.iloc[-1]
        current_histogram = histogram.iloc[-1]
        
        if current_macd > current_signal:
            signal = "bullish"
        else:
            signal = "bearish"
            
        return round(current_macd, 4), round(current_signal, 4), round(current_histogram, 4), signal
    
    def calculate_stochastic(self, highs: List[float], lows: List[float], closes: List[float]) -> Tuple[float, float, str]:
        """
        Расчет Stochastic Oscillator
        Выше 80 - перекуплен, ниже 20 - перепродан
        """
        if len(closes) < self.stoch_period:
            return None, None, "no_data"
        
        # Используем упрощенный расчет Fast Stochastic
        highest_high = max(highs[-self.stoch_period:])
        lowest_low = min(lows[-self.stoch_period:])
        
        current_close = closes[-1]
        
        if highest_high == lowest_low:
            stoch_k = 50
        else:
            stoch_k = ((current_close - lowest_low) / (highest_high - lowest_low)) * 100
        
        # Простая скользящая средняя для %D
        if len(closes) >= self.stoch_period + 3:
            closes_window = closes[-(self.stoch_period + 3):]
            highs_window = highs[-(self.stoch_period + 3):]
            lows_window = lows[-(self.stoch_period + 3):]
            
            k_values = []
            for i in range(len(closes_window) - self.stoch_period):
                hh = max(highs_window[i:i + self.stoch_period])
                ll = min(lows_window[i:i + self.stoch_period])
                if hh == ll:
                    k_values.append(50)
                else:
                    k_values.append(((closes_window[i + self.stoch_period - 1] - ll) / (hh - ll)) * 100)
            
            if k_values:
                stoch_d = np.mean(k_values[-3:])
            else:
                stoch_d = stoch_k
        else:
            stoch_d = stoch_k
        
        if stoch_k >= 80:
            signal = "overbought"
        elif stoch_k <= 20:
            signal = "oversold"
        else:
            signal = "neutral"
            
        return round(stoch_k, 2), round(stoch_d, 2), signal
    
    def calculate_cci(self, highs: List[float], lows: List[float], closes: List[float]) -> Tuple[float, str]:
        """
        Расчет CCI (Commodity Channel Index)
        Выше +100 - перекуплен, ниже -100 - перепродан
        """
        if len(closes) < self.cci_period:
            return None, "no_data"
        
        typical_prices = [(h + l + c) / 3 for h, l, c in zip(highs, lows, closes)]
        tp_window = typical_prices[-self.cci_period:]
        
        tp_mean = np.mean(tp_window)
        tp_mean_deviation = np.mean([abs(tp - tp_mean) for tp in tp_window])
        
        if tp_mean_deviation == 0:
            cci = 0
        else:
            cci = (tp_window[-1] - tp_mean) / (0.015 * tp_mean_deviation)
        
        if cci >= 100:
            signal = "overbought"
        elif cci <= -100:
            signal = "oversold"
        else:
            signal = "neutral"
            
        return round(cci, 2), signal
    
    def calculate_williams_r(self, highs: List[float], lows: List[float], closes: List[float]) -> Tuple[float, str]:
        """
        Расчет Williams %R
        Выше -20 - перекуплен, ниже -80 - перепродан
        """
        if len(closes) < self.williams_period:
            return None, "no_data"
        
        highest_high = max(highs[-self.williams_period:])
        lowest_low = min(lows[-self.williams_period:])
        
        if highest_high == lowest_low:
            williams_r = -50
        else:
            williams_r = ((highest_high - closes[-1]) / (highest_high - lowest_low)) * (-100)
        
        if williams_r >= -20:
            signal = "overbought"
        elif williams_r <= -80:
            signal = "oversold"
        else:
            signal = "neutral"
            
        return round(williams_r, 2), signal
    
    def calculate_mfi(self, highs: List[float], lows: List[float], closes: List[float], volumes: List[float]) -> Tuple[float, str]:
        """
        Расчет MFI (Money Flow Index)
        Выше 80 - перекуплен, ниже 20 - перепродан
        """
        if len(closes) < self.mfi_period + 1:
            return None, "no_data"
        
        typical_prices = [(h + l + c) / 3 for h, l, c in zip(highs, lows, closes)]
        money_flows = [tp * v for tp, v in zip(typical_prices, volumes)]
        
        positive_flow = []
        negative_flow = []
        
        for i in range(1, len(typical_prices)):
            if typical_prices[i] > typical_prices[i-1]:
                positive_flow.append(money_flows[i])
                negative_flow.append(0)
            elif typical_prices[i] < typical_prices[i-1]:
                positive_flow.append(0)
                negative_flow.append(money_flows[i])
            else:
                positive_flow.append(0)
                negative_flow.append(0)
        
        pos_window = positive_flow[-self.mfi_period:]
        neg_window = negative_flow[-self.mfi_period:]
        
        money_ratio = sum(pos_window) / (sum(neg_window) if sum(neg_window) != 0 else 1)
        mfi = 100 - (100 / (1 + money_ratio))
        
        if mfi >= 80:
            signal = "overbought"
        elif mfi <= 20:
            signal = "oversold"
        else:
            signal = "neutral"
            
        return round(mfi, 2), signal
    
    def calculate_ultimate_oscillator(self, highs: List[float], lows: List[float], closes: List[float]) -> Tuple[float, str]:
        """
        Расчет Ultimate Oscillator
        Выше 70 - перекуплен, ниже 30 - перепродан
        """
        if len(closes) < 28:
            return None, "no_data"
        
        def calc_bp_tr(period, offset):
            bp = 0
            tr = 0
            for i in range(-offset-period, -offset):
                bp += closes[i] - min(lows[i], closes[i-1] if i-1 >= -len(closes) else closes[i])
                tr += max(highs[i], closes[i-1] if i-1 >= -len(closes) else closes[i]) - min(lows[i], closes[i-1] if i-1 >= -len(closes) else closes[i])
            return bp, tr
        
        bp7, tr7 = calc_bp_tr(7, 0)
        bp14, tr14 = calc_bp_tr(14, 0)
        bp28, tr28 = calc_bp_tr(28, 0)
        
        avg7 = bp7 / tr7 if tr7 != 0 else 0
        avg14 = bp14 / tr14 if tr14 != 0 else 0
        avg28 = bp28 / tr28 if tr28 != 0 else 0
        
        uo = 100 * ((4 * avg7) + (2 * avg14) + avg28) / 7
        
        if uo >= 70:
            signal = "overbought"
        elif uo <= 30:
            signal = "oversold"
        else:
            signal = "neutral"
            
        return round(uo, 2), signal
    
    def calculate_atr(self, highs: List[float], lows: List[float], closes: List[float]) -> float:
        """
        Расчет ATR (Average True Range)
        """
        if len(closes) < self.atr_period + 1:
            return None
        
        true_ranges = []
        for i in range(1, len(highs)):
            tr = max(
                highs[i] - lows[i],
                abs(highs[i] - closes[i-1]),
                abs(lows[i] - closes[i-1])
            )
            true_ranges.append(tr)
        
        atr = np.mean(true_ranges[-self.atr_period:])
        return round(atr, 4)
    
    def calculate_bollinger_bands(self, closes: List[float]) -> Tuple[float, float, float, str]:
        """
        Расчет Bollinger Bands
        """
        if len(closes) < self.bb_period:
            return None, None, None, "no_data"
        
        window = closes[-self.bb_period:]
        middle = np.mean(window)
        std = np.std(window)
        
        upper = middle + (2 * std)
        lower = middle - (2 * std)
        
        current_close = closes[-1]
        
        if current_close > upper:
            position = "above_upper"
        elif current_close < lower:
            position = "below_lower"
        else:
            position = "between"
            
        return round(upper, 2), round(middle, 2), round(lower, 2), position
    
    def calculate_overall_score(self, oscillator_data: Dict) -> Dict:
        """
        Расчет общего скорр балла на основе всех осцилляторов
        
        Каждый осциллятор дает баллы:
        -2: сильный сигнал на продажу
        -1: сигнал на продажу
        0: нейтральный
        +1: сигнал на покупку
        +2: сильный сигнал на покупку
        """
        score = 0
        details = []
        
        # RSI scoring
        if oscillator_data.get('rsi_signal') == 'oversold':
            score += 2
            details.append("RSI: перепродан (+2)")
        elif oscillator_data.get('rsi_signal') == 'overbought':
            score -= 2
            details.append("RSI: перекуплен (-2)")
        else:
            details.append("RSI: нейтрально (0)")
        
        # MACD scoring
        if oscillator_data.get('macd_signal') == 'bullish':
            score += 1
            details.append("MACD: бычий (+1)")
        elif oscillator_data.get('macd_signal') == 'bearish':
            score -= 1
            details.append("MACD: медвежий (-1)")
        
        # Stochastic scoring
        if oscillator_data.get('stoch_signal') == 'oversold':
            score += 2
            details.append("Stochastic: перепродан (+2)")
        elif oscillator_data.get('stoch_signal') == 'overbought':
            score -= 2
            details.append("Stochastic: перекуплен (-2)")
        else:
            details.append("Stochastic: нейтрально (0)")
        
        # CCI scoring
        if oscillator_data.get('cci_signal') == 'oversold':
            score += 1
            details.append("CCI: перепродан (+1)")
        elif oscillator_data.get('cci_signal') == 'overbought':
            score -= 1
            details.append("CCI: перекуплен (-1)")
        else:
            details.append("CCI: нейтрально (0)")
        
        # Williams %R scoring
        if oscillator_data.get('williams_r_signal') == 'oversold':
            score += 2
            details.append("Williams %R: перепродан (+2)")
        elif oscillator_data.get('williams_r_signal') == 'overbought':
            score -= 2
            details.append("Williams %R: перекуплен (-2)")
        else:
            details.append("Williams %R: нейтрально (0)")
        
        # MFI scoring
        if oscillator_data.get('mfi_signal') == 'oversold':
            score += 2
            details.append("MFI: перепродан (+2)")
        elif oscillator_data.get('mfi_signal') == 'overbought':
            score -= 2
            details.append("MFI: перекуплен (-2)")
        else:
            details.append("MFI: нейтрально (0)")
        
        # Ultimate Oscillator scoring
        if oscillator_data.get('uo_signal') == 'oversold':
            score += 2
            details.append("Ultimate Oscillator: перепродан (+2)")
        elif oscillator_data.get('uo_signal') == 'overbought':
            score -= 2
            details.append("Ultimate Oscillator: перекуплен (-2)")
        else:
            details.append("Ultimate Oscillator: нейтрально (0)")
        
        # Bollinger Bands scoring
        if oscillator_data.get('bb_position') == 'below_lower':
            score += 2
            details.append("Bollinger Bands: цена ниже нижней полосы (+2)")
        elif oscillator_data.get('bb_position') == 'above_upper':
            score -= 2
            details.append("Bollinger Bands: цена выше верхней полосы (-2)")
        else:
            details.append("Bollinger Bands: в пределах полос (0)")
        
        # Определение общего сигнала
        if score >= 6:
            signal = "STRONG BUY"
        elif score >= 3:
            signal = "BUY"
        elif score <= -6:
            signal = "STRONG SELL"
        elif score <= -3:
            signal = "SELL"
        else:
            signal = "NEUTRAL"
        
        return {
            'score': score,
            'signal': signal,
            'details': details
        }
    
    def analyze_all(self, klines_data: List[Dict]) -> Dict:
        """
        Комплексный анализ всех осцилляторов
        """
        closes = [k['close'] for k in klines_data]
        highs = [k['high'] for k in klines_data]
        lows = [k['low'] for k in klines_data]
        volumes = [k['volume'] for k in klines_data]
        
        result = {
            'timestamp': klines_data[-1]['open_time'],
            'symbol': 'ETHUSDT',
            'current_price': closes[-1]
        }
        
        # Расчет всех осцилляторов
        rsi_value, rsi_signal = self.calculate_rsi(closes)
        result['rsi'] = rsi_value
        result['rsi_signal'] = rsi_signal
        
        macd, macd_signal_line, macd_hist, macd_signal = self.calculate_macd(closes)
        result['macd'] = macd
        result['macd_signal_line'] = macd_signal_line
        result['macd_histogram'] = macd_hist
        result['macd_signal'] = macd_signal
        
        stoch_k, stoch_d, stoch_signal = self.calculate_stochastic(highs, lows, closes)
        result['stoch_k'] = stoch_k
        result['stoch_d'] = stoch_d
        result['stoch_signal'] = stoch_signal
        
        cci, cci_signal = self.calculate_cci(highs, lows, closes)
        result['cci'] = cci
        result['cci_signal'] = cci_signal
        
        williams_r, wr_signal = self.calculate_williams_r(highs, lows, closes)
        result['williams_r'] = williams_r
        result['williams_r_signal'] = wr_signal
        
        mfi, mfi_signal = self.calculate_mfi(highs, lows, closes, volumes)
        result['mfi'] = mfi
        result['mfi_signal'] = mfi_signal
        
        uo, uo_signal = self.calculate_ultimate_oscillator(highs, lows, closes)
        result['ultimate_oscillator'] = uo
        result['uo_signal'] = uo_signal
        
        atr = self.calculate_atr(highs, lows, closes)
        result['atr'] = atr
        
        bb_upper, bb_middle, bb_lower, bb_position = self.calculate_bollinger_bands(closes)
        result['bb_upper'] = bb_upper
        result['bb_middle'] = bb_middle
        result['bb_lower'] = bb_lower
        result['bb_position'] = bb_position
        
        # Расчет общего скора
        overall = self.calculate_overall_score(result)
        result['overall_score'] = overall['score']
        result['overall_signal'] = overall['signal']
        result['score_details'] = overall['details']
        
        return result

oscillator_analyzer = OscillatorAnalyzer()