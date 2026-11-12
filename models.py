# models.py (без изменений)
from sqlalchemy import Column, Integer, String, Float, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func

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
        return f"<KlineData(symbol={self.symbol}, open_time={self.open_time})>"


class OscillatorData(Base):
    __tablename__ = 'oscillator_data'
    id = Column(Integer, primary_key=True, autoincrement=True)
    kline_id = Column(Integer, nullable=False, index=True)
    symbol = Column(String(20), nullable=False)
    timestamp = Column(DateTime, nullable=False, index=True)

    # RSI
    rsi = Column(Float, nullable=True)
    rsi_signal = Column(String(20), nullable=True)

    # MACD
    macd = Column(Float, nullable=True)
    macd_signal_line = Column(Float, nullable=True)
    macd_histogram = Column(Float, nullable=True)
    macd_signal = Column(String(20), nullable=True)

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
    bb_position = Column(String(20), nullable=True)

    # Общий скор
    overall_score = Column(Float, nullable=True)
    overall_signal = Column(String(20), nullable=True)

    created_at = Column(DateTime, server_default=func.now())

    def __repr__(self):
        return f"<OscillatorData(symbol={self.symbol}, timestamp={self.timestamp})>"

# models.py (дополнение)

class DerivativesSnapshot(Base):
    """Периодический снимок деривативных метрик OKX."""
    __tablename__ = 'derivatives_snapshots'

    id = Column(Integer, primary_key=True, autoincrement=True)
    symbol = Column(String(20), nullable=False)          # btc, eth (внутренний id)
    inst_id = Column(String(30), nullable=False)          # BTC-USDT-SWAP
    timestamp = Column(DateTime, nullable=False, index=True)
    funding_rate = Column(Float, nullable=True)
    open_interest_contracts = Column(Float, nullable=True)
    open_interest_usd = Column(Float, nullable=True)      # notional
    long_short_ratio = Column(Float, nullable=True)
    taker_buy_volume = Column(Float, nullable=True)
    taker_sell_volume = Column(Float, nullable=True)
    volume_usd = Column(Float, nullable=True)
    source = Column(String(20), nullable=False, default='okx')
    created_at = Column(DateTime, server_default=func.now())

    def __repr__(self):
        return f"<DerivativesSnapshot {self.symbol} {self.timestamp}>"


class FundingEvent(Base):
    """Исторические события сеттлмента funding rate."""
    __tablename__ = 'funding_events'

    id = Column(Integer, primary_key=True, autoincrement=True)
    symbol = Column(String(20), nullable=False)
    inst_id = Column(String(30), nullable=False)
    funding_time = Column(DateTime, nullable=False, index=True)
    realized_rate = Column(Float, nullable=False)
    source = Column(String(20), nullable=False, default='okx')
    created_at = Column(DateTime, server_default=func.now())

    def __repr__(self):
        return f"<FundingEvent {self.symbol} {self.funding_time}>"


class LiquidationEvent(Base):
    """События ликвидаций (опционально, через WebSocket)."""
    __tablename__ = 'liquidation_events'

    id = Column(Integer, primary_key=True, autoincrement=True)
    symbol = Column(String(20), nullable=False)
    inst_id = Column(String(30), nullable=False)
    timestamp = Column(DateTime, nullable=False, index=True)
    pos_side = Column(String(10), nullable=False)          # long / short
    price = Column(Float, nullable=False)
    size_contracts = Column(Float, nullable=False)
    size_usd = Column(Float, nullable=True)
    source = Column(String(20), nullable=False, default='okx')
    created_at = Column(DateTime, server_default=func.now())

    def __repr__(self):
        return f"<LiquidationEvent {self.symbol} {self.timestamp}>"