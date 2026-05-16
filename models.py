from sqlalchemy import Column, Integer, String, Float, DateTime, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func
from datetime import datetime

Base = declarative_base()

class KlineData(Base):
    __tablename__ = 'kline_data'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    symbol = Column(String(20), nullable=False)
    open_time = Column(DateTime, nullable=False, index=True)
    close_time = Column(DateTime, nullable=False)
    open_price = Column(Float, nullable=False)
    high_price = Column(Float, nullable=False)
    low_price = Column(Float, nullable=False)
    close_price = Column(Float, nullable=False)
    volume = Column(Float, nullable=False)
    quote_volume = Column(Float, nullable=False)
    trades_count = Column(Integer, nullable=False)
    created_at = Column(DateTime, server_default=func.now())
    
    def __repr__(self):
        return f"<KlineData(symbol={self.symbol}, open_time={self.open_time}, close_price={self.close_price})>"

class OscillatorData(Base):
    __tablename__ = 'oscillator_data'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    kline_id = Column(Integer, nullable=False, index=True)
    symbol = Column(String(20), nullable=False)
    timestamp = Column(DateTime, nullable=False, index=True)
    
    # RSI
    rsi = Column(Float, nullable=True)
    rsi_signal = Column(String(20), nullable=True)  # overbought, oversold, neutral
    
    # MACD
    macd = Column(Float, nullable=True)
    macd_signal_line = Column(Float, nullable=True)
    macd_histogram = Column(Float, nullable=True)
    macd_signal = Column(String(20), nullable=True)  # bullish, bearish
    
    # Stochastic
    stoch_k = Column(Float, nullable=True)
    stoch_d = Column(Float, nullable=True)
    stoch_signal = Column(String(20), nullable=True)
    
    # CCI
    cci = Column(Float, nullable=True)
    cci_signal = Column(String(20), nullable=True)
    
    # Williams %R
    williams_r = Column(Float, nullable=True)
    williams_r_signal = Column(String(20), nullable=True)
    
    # MFI
    mfi = Column(Float, nullable=True)
    mfi_signal = Column(String(20), nullable=True)
    
    # Ultimate Oscillator
    ultimate_oscillator = Column(Float, nullable=True)
    uo_signal = Column(String(20), nullable=True)
    
    # ATR
    atr = Column(Float, nullable=True)
    
    # Bollinger Bands
    bb_upper = Column(Float, nullable=True)
    bb_middle = Column(Float, nullable=True)
    bb_lower = Column(Float, nullable=True)
    bb_position = Column(String(20), nullable=True)  # above_upper, between, below_lower
    
    # Общий скорр балл
    overall_score = Column(Float, nullable=True)  # от -8 до +8
    overall_signal = Column(String(20), nullable=True)  # strong_buy, buy, neutral, sell, strong_sell
    
    created_at = Column(DateTime, server_default=func.now())
    
    def __repr__(self):
        return f"<OscillatorData(timestamp={self.timestamp}, score={self.overall_score}, signal={self.overall_signal})>"