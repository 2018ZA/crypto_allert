# clients/factory.py
from .okx_client import OKXClient
from .binance_client import BinanceClient

_CLIENTS = {
    "okx": OKXClient,
    "binance": BinanceClient,
}


def get_client(source: str):
    cls = _CLIENTS.get(source.lower())
    if cls is None:
        raise ValueError(
            f"Неизвестный источник данных: {source!r}. "
            f"Доступные: {list(_CLIENTS)}"
        )
    return cls()