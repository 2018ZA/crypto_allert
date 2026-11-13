# 🔮 Crypto Oscillator Analyzer

Профессиональный анализатор криптовалютного рынка с расчётом технических осцилляторов, сбором деривативных метрик (funding rate, open interest, long/short ratio, taker volume, ликвидации) и автоматической отправкой сигналов в Telegram.

[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://www.python.org/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-15-blue.svg)](https://www.postgresql.org/)
[![Binance](https://img.shields.io/badge/Binance-API-yellow.svg)](https://www.binance.com/)
[![OKX](https://img.shields.io/badge/OKX-API-black.svg)](https://www.okx.com/)
[![Telegram](https://img.shields.io/badge/Telegram-Bot-blue.svg)](https://core.telegram.org/bots)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

## 📋 Содержание

- [Возможности](#-возможности)
- [Архитектура проекта](#-архитектура-проекта)
- [Технический стек](#-технический-стек)
- [Установка и настройка](#-установка-и-настройка)
- [Использование](#-использование)
- [Осцилляторы и сигналы](#-осцилляторы-и-сигналы)
- [База данных](#-база-данных)
- [API Binance и OKX](#-api-binance-и-okx)
- [Деривативные метрики OKX](#-деривативные-метрики-okx)
- [Telegram интеграция](#-telegram-интеграция)
- [Система скоринга](#-система-скоринга)
- [Скрипты и утилиты](#-скрипты-и-утилиты)
- [Логирование](#-логирование)
- [Безопасность](#-безопасность)
- [Решение проблем](#-решение-проблем)
- [Разработка](#-разработка)
- [Лицензия](#-лицензия)

## 🚀 Возможности

- 📊 **Автоматический сбор данных** с Binance/OKX API каждый час
- 💾 **Сохранение истории** в PostgreSQL (свечи + осцилляторы + деривативы)
- 📈 **Расчёт 9 технических осцилляторов**
- 🎯 **Скоринговая система** (−14 до +14 баллов)
- 🔮 **Деривативные метрики OKX**: funding rate, open interest, long/short ratio, taker volume, ликвидации
- ⚡ **Автоматический догон истории** при пропуске данных (рестарт, сбой)
- 🤖 **Telegram бот** для автоматических уведомлений
- 📝 **Подробное логирование** всех операций
- 🔄 **Умная проверка** — не запрашивает данные, если они актуальны
- 🐳 **Docker поддержка** для PostgreSQL
- 🔌 **Pluggable data sources**: переключение Binance ↔ OKX через `DATA_SOURCE`

## 🏗 Архитектура проекта

### Структура файлов

| Файл | Назначение | Ключевые компоненты |
|------|------------|---------------------|
| `config.py` | Конфигурация приложения | Настройки БД, Telegram, Binance/OKX API, интервалы обновления, деривативы |
| `database.py` | Работа с PostgreSQL | Подключение к БД, CRUD операции, создание таблиц, сессии |
| `models.py` | SQLAlchemy модели | KlineData, OscillatorData, DerivativesSnapshot, FundingEvent, LiquidationEvent |
| `clients/base_client.py` | ABC-интерфейс источника данных | MarketDataClient, fetch_candles, fetch_funding_history |
| `clients/binance_client.py` | Клиент Binance API | Запросы к API, получение свечей |
| `clients/okx_client.py` | Клиент OKX API | Свечи + funding, OI, L/S ratio, taker volume, ликвидации |
| `clients/factory.py` | Фабрика клиентов | `get_client(DATA_SOURCE)` |
| `oscillators.py` | Расчёт осцилляторов | RSI, MACD, Stochastic, CCI, Williams %R, MFI, UO, ATR, BB |
| `telegram_sender.py` | Отправка в Telegram | Форматирование сообщений, отправка в канал |
| `main.py` | Главный файл приложения | Планировщик, оркестрация, `process_update`, `sync_derivatives` |
| `backfill_oscillators.py` | Досчёт осцилляторов | Заполнение пропусков в `oscillator_data` |
| `requirements.txt` | Зависимости Python | Список всех необходимых пакетов |
| `.env.example` | Пример конфигурации | Шаблон переменных окружения |
| `docker-compose.yml` | Docker для PostgreSQL | Контейнер с PostgreSQL 15 |
| `README.md` | Документация | Полное описание проекта |

### Детальное описание модулей

| Модуль | Классы | Основные методы | Зависимости |
|--------|--------|-----------------|-------------|
| `config.py` | `Config` | `database_url` (property) | python-dotenv |
| `database.py` | `Database` | `create_tables()`, `get_session()`, `save_kline_data()`, `save_oscillator_data()`, `get_last_klines()`, `get_latest_kline_id()`, `save_derivatives_snapshot()`, `save_funding_events()`, `save_liquidation_events()` | SQLAlchemy, models |
| `models.py` | `KlineData`, `OscillatorData`, `DerivativesSnapshot`, `FundingEvent`, `LiquidationEvent` | SQLAlchemy модели (наследуют `Base`) | SQLAlchemy |
| `clients/base_client.py` | `MarketDataClient` (ABC) | `fetch_candles()`, `is_available()`, `fetch_derivatives_snapshot()`, `fetch_funding_history()`, `fetch_liquidations()` | abc |
| `clients/binance_client.py` | `BinanceClient` | `fetch_klines(limit)`, `is_available()` | requests |
| `clients/okx_client.py` | `OKXClient` | `fetch_candles()`, `_get_funding_rate()`, `_get_open_interest()`, `_get_taker_volume_contract()`, `_get_long_short_ratio()`, `fetch_funding_history()`, `fetch_liquidations()` | requests |
| `clients/factory.py` | — | `get_client(source)` | config, clients |
| `oscillators.py` | `OscillatorAnalyzer` | `analyze_all()`, `calculate_rsi()`, `calculate_macd()`, `calculate_stochastic()`, `calculate_cci()`, `calculate_williams_r()`, `calculate_mfi()`, `calculate_ultimate_oscillator()`, `calculate_atr()`, `calculate_bollinger_bands()`, `calculate_overall_score()` | numpy, pandas |
| `telegram_sender.py` | `TelegramSender` | `send_message()`, `format_message()`, `_format_signal()` | requests |
| `main.py` | `CryptoAnalyzerApp` | `initialize()`, `process_update()`, `sync_derivatives()`, `get_latest_kline()`, `run_once()`, `start_scheduler()`, `_filter_oscillator_fields()` | Все модули |
| `backfill_oscillators.py` | — | CLI-скрипт досчёта осцилляторов | database, oscillators |

### Поток данных между модулями — основной цикл

| Шаг | Модуль | Действие | Входные данные | Выходные данные |
|-----|--------|----------|----------------|-----------------|
| 1 | `main.py` | Запуск таймера | Интервал из `config.py` | Сигнал к обновлению |
| 2 | `clients/*` | Запрос к API | SYMBOL, INTERVAL, LIMIT | Список свечей (JSON) |
| 3 | `database.py` | Сохранение в БД | Список свечей | ID записей |
| 4 | `database.py` | Чтение из БД | LIMIT=100 | 100 последних свечей |
| 5 | `oscillators.py` | Расчёт осцилляторов | Свечи (100 шт.) | Словарь с 9 осцилляторами |
| 6 | `database.py` | Сохранение осцилляторов | Словарь осцилляторов | ID записи |
| 7 | `oscillators.py` | Расчёт общего скора | Словарь осцилляторов | Score + Signal |
| 8 | `telegram_sender.py` | Отправка сообщения | Результаты анализа | Сообщение в Telegram |

### Поток данных — сбор деривативов (`sync_derivatives`, каждые 15 мин)

| Шаг | Модуль | Действие | Входные данные | Выходные данные |
|-----|--------|----------|----------------|-----------------|
| 1 | `main.py` | Таймер 15 мин | `DERIVATIVES_SYNC_INTERVAL_MIN` | Сигнал к запуску |
| 2 | `clients/okx_client.py` | GET funding-rate | instId | `{rate, fundingTime}` |
| 3 | `clients/okx_client.py` | GET open-interest | instId | `{oi, oiUsd, ts}` |
| 4 | `clients/okx_client.py` | GET long-short-account-ratio | ccy, period | `[[ts, ratio]]` |
| 5 | `clients/okx_client.py` | GET taker-volume-contract | instId, period | `[[ts, sell, buy]]` |
| 6 | `clients/okx_client.py` | GET funding-rate-history | instId, limit=100 | 100 событий |
| 7 | `clients/okx_client.py` | GET liquidation-orders | instId, uly | До 100 событий |
| 8 | `database.py` | UPSERT в 3 таблицы | Нормализованные данные | Строки в `derivatives_snapshots`, `funding_events`, `liquidation_events` |

### Переменные окружения (.env)

| Переменная | По умолчанию | Описание | Обязательная |
|------------|--------------|----------|--------------|
| `DATA_SOURCE` | okx | Источник: `okx` или `binance` | Да |
| `DB_HOST` | localhost | Хост PostgreSQL | Да |
| `DB_PORT` | 5432 | Порт PostgreSQL | Да |
| `DB_NAME` | crypto_analyzer | Имя базы данных | Да |
| `DB_USER` | postgres | Пользователь БД | Да |
| `DB_PASSWORD` | (пусто) | Пароль БД | Да |
| `TELEGRAM_BOT_TOKEN` | (пусто) | Токен Telegram бота | Нет* |
| `TELEGRAM_CHANNEL_ID` | (пусто) | ID/username канала | Нет* |
| `UPDATE_INTERVAL_HOURS` | 1 | Интервал обновления основного цикла | Да |
| `DERIVATIVES_ENABLED` | true | Включить сбор деривативов | Да |
| `DERIVATIVES_PERIOD` | 1H | Период rubik-эндпоинтов (`5m`, `15m`, `1H`, `4H`, `1D`) | Да |
| `DERIVATIVES_SYNC_INTERVAL_MIN` | 15 | Период `sync_derivatives` (мин) | Да |
| `FUNDING_HISTORY_LIMIT` | 100 | Сколько событий funding при backfill | Да |

*Telegram настройки не обязательны для тестового режима.

### Константы и параметры

| Параметр | Значение | Файл | Описание |
|----------|----------|------|----------|
| `INSTRUMENTS` | 13 инструментов | config.py | Список торговых пар (crypto + металлы) |
| `INTERVAL` | 1h | config.py | Интервал свечей |
| `BINANCE_API_URL` | api.binance.com/api/v3/klines | config.py | URL Binance API |
| `OKX_BASE_URL` | www.okx.com/api/v5 | okx_client.py | URL OKX V5 API |
| `LIMIT` | 100 | config.py | Количество запрашиваемых свечей |
| `RSI_PERIOD` | 14 | oscillators.py | Период RSI |
| `MACD_FAST` | 12 | oscillators.py | Быстрая EMA MACD |
| `MACD_SLOW` | 26 | oscillators.py | Медленная EMA MACD |
| `MACD_SIGNAL` | 9 | oscillators.py | Сигнальная линия MACD |
| `STOCH_PERIOD` | 14 | oscillators.py | Период Stochastic |
| `CCI_PERIOD` | 20 | oscillators.py | Период CCI |
| `WILLIAMS_PERIOD` | 14 | oscillators.py | Период Williams %R |
| `MFI_PERIOD` | 14 | oscillators.py | Период MFI |
| `ATR_PERIOD` | 14 | oscillators.py | Период ATR |
| `BB_PERIOD` | 20 | oscillators.py | Период Bollinger Bands |
| `MIN_KLINES` | 28 | main.py | Минимум свечей для анализа |

## 🔄 Поток данных — основной цикл

### Детализация каждого шага

| Шаг | API / Функция | Параметры | Пример запроса / Код | Пример ответа |
|-----|---------------|-----------|---------------------|---------------|
| 1 | `schedule.every(1).hours.do()` | `UPDATE_INTERVAL_HOURS=1` | `schedule.every(1).hours.do(process_update)` | Запуск `process_update()` |
| 2 | `GET /api/v3/klines` или `/api/v5/market/candles` | `symbol=ETHUSDT`<br>`interval=1h`<br>`limit=1` | `https://api.binance.com/api/v3/klines?symbol=ETHUSDT&interval=1h&limit=1` | `[[1499040000000, "0.01634790", ...]]` |
| 3 | `save_kline_data()` | `kline_list` — список свечей | `db.save_kline_data(klines)` | `INFO: Сохранена свеча за 2026-11-13 02:00:00` |
| 4 | `analyze_all()` | `klines_data` — 100 свечей | `oscillator_analyzer.analyze_all(klines_from_db)` | `{rsi: 45.23, macd: 2.15, ...}` |
| 5 | `save_oscillator_data()` | `osc_data` — словарь осцилляторов | `db.save_oscillator_data(oscillator_fields, latest_kline_id)` | `INFO: Сохранены данные осцилляторов для свечи 123` |
| 6 | `calculate_overall_score()` | `oscillator_data` — значения осцилляторов | `score = oscillator_analyzer.calculate_overall_score(result)` | `{score: 7, signal: "BUY"}` |
| 7 | `send_message()` | `data` — полный анализ | `telegram_sender.send_message(analysis_result)` | `INFO: Сообщение успешно отправлено в Telegram` |

### Обработка ошибок на каждом шаге

| Шаг | Возможная ошибка | Обработка | Действие |
|-----|------------------|-----------|----------|
| 1 | Таймер не запустился | `try/except` в `start_scheduler()` | Логирование, повторная попытка |
| 2 | Сетевая ошибка / API недоступен | `try/except` в `fetch_candles()` | Логирование ERROR, пропуск цикла |
| 3 | Ошибка записи в БД | `try/except` в `save_kline_data()` | Логирование, rollback транзакции |
| 4 | Недостаточно данных (< 28 свечей) | Проверка `len(klines) < 28` | WARNING, пропуск анализа |
| 5 | Ошибка сохранения осцилляторов | `try/except` в `save_oscillator_data()` | Логирование, rollback |
| 6 | Ошибка в расчёте скора | `try/except` в `calculate_overall_score()` | Возврат нейтрального сигнала |
| 7 | Ошибка отправки в Telegram | `try/except` в `send_message()` | Логирование WARNING (не критично) |

## 🛠 Технический стек

| Технология | Версия | Назначение |
|------------|--------|------------|
| Python | 3.8+ | Основной язык программирования |
| PostgreSQL | 15 | Реляционная база данных |
| SQLAlchemy | 2.0+ | ORM для работы с БД (2.0-style API: `select()` + `session.execute()`) |
| psycopg2-binary | 2.9+ | PostgreSQL драйвер |
| Requests | 2.31+ | HTTP запросы к Binance/OKX API |
| Pandas | 2.1+ | Обработка и анализ данных |
| NumPy | 1.26+ | Математические вычисления |
| Schedule | 1.2+ | Планировщик задач |
| python-dotenv | 1.0+ | Переменные окружения |

> ⚠️ **Важно:** начиная с SQLAlchemy 2.0 методы `Query.unique()` и `Query.distinct(column)` **удалены**. Все запросы в проекте используют современный API: `select()` + `session.execute()`. Legacy `session.query()` не используется.

## 📦 Установка и настройка

### Предварительные требования

- Python 3.8 или выше
- PostgreSQL 15 или Docker
- Git
- Telegram Bot Token (опционально)
- API-ключ OKX **не требуется** — все деривативные эндпоинты публичные

### Шаг 1: Клонирование репозитория

```bash
git clone <your-repo-url>
cd crypto_analyzer
```

### Шаг 2: Установка зависимостей

```bash
python -m venv venv
source venv/bin/activate  # Linux/macOS
pip install -r requirements.txt
```

### Шаг 3: Настройка базы данных

**Вариант А: Локальный PostgreSQL**

```bash
# macOS
brew install postgresql@15
brew services start postgresql@15
createdb crypto_analyzer

# Linux (Ubuntu/Debian)
sudo apt install postgresql postgresql-contrib
sudo systemctl start postgresql
sudo -u postgres createdb crypto_analyzer
```

**Вариант Б: Docker**

```bash
docker-compose up -d
docker ps
docker logs crypto_analyzer_db
```

### Шаг 4: Конфигурация

```bash
cp .env.example .env
nano .env
```

Пример `.env`:

```
# База данных
DB_HOST=localhost
DB_PORT=5432
DB_NAME=crypto_analyzer
DB_USER=postgres
DB_PASSWORD=your_password_here

# Telegram
TELEGRAM_BOT_TOKEN=123456789:ABCdefGHIjklMNOpqrsTUVwxyz
TELEGRAM_CHANNEL_ID=@your_channel_username

# Приложение
DATA_SOURCE=okx
UPDATE_INTERVAL_HOURS=1

# Деривативы
DERIVATIVES_ENABLED=true
DERIVATIVES_PERIOD=1H
DERIVATIVES_SYNC_INTERVAL_MIN=15
FUNDING_HISTORY_LIMIT=100
```

### Шаг 5: Проверка установки

```bash
# Проверка подключения к БД
psql -h localhost -U postgres -d crypto_analyzer -c "\conninfo"

# Тестовый запуск
python main.py --test
```

Таблицы создаются автоматически при первом запуске (`db.create_tables()` в `CryptoAnalyzerApp.initialize()`). Миграции через Alembic не используются — схема поддерживается через SQLAlchemy ORM.

## 🚀 Использование

### Режимы запуска

```bash
# Запуск планировщика (обновление каждый час + деривативы каждые 15 мин)
python main.py

# Однократное выполнение
python main.py --once

# Тестовый запуск (вывод в консоль, без Telegram)
python main.py --test
```

### Демонизация (Linux) — systemd

Создайте файл `/etc/systemd/system/crypto-analyzer.service`:

```ini
[Unit]
Description=Crypto Oscillator Analyzer
After=network.target postgresql.service

[Service]
Type=simple
User=root
WorkingDirectory=/root/crypto_allert
EnvironmentFile=/root/crypto_allert/.env
ExecStart=/root/crypto_allert/venv/bin/python main.py
Restart=on-failure
RestartSec=10
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl daemon-reload
sudo systemctl enable crypto-analyzer
sudo systemctl start crypto-analyzer
sudo systemctl status crypto-analyzer

# Логи
sudo journalctl -u crypto-analyzer -f
sudo journalctl -u crypto-analyzer --since "1 hour ago" | grep -iE "error|traceback"
```

### Проверка работоспособности

```bash
# 1. Процесс жив
sudo systemctl is-active crypto-analyzer

# 2. Логи без ошибок
sudo journalctl -u crypto-analyzer --since "10 minutes ago" --no-pager | grep -iE "error|traceback"

# 3. Данные идут
cd /root/crypto_allert && venv/bin/python -c "
from database import db
from models import KlineData, OscillatorData, DerivativesSnapshot, FundingEvent, LiquidationEvent
from sqlalchemy import select, func
with db.get_session() as s:
    print(f'klines:              {s.execute(select(func.count()).select_from(KlineData)).scalar()}')
    print(f'oscillators:         {s.execute(select(func.count()).select_from(OscillatorData)).scalar()}')
    print(f'derivatives:         {s.execute(select(func.count()).select_from(DerivativesSnapshot)).scalar()}')
    print(f'funding_events:      {s.execute(select(func.count()).select_from(FundingEvent)).scalar()}')
    print(f'liquidation_events:  {s.execute(select(func.count()).select_from(LiquidationEvent)).scalar()}')
"
```

## 📊 Осцилляторы и сигналы

### Список рассчитываемых осцилляторов

| № | Осциллятор | Период | Перекупленность | Перепроданность |
|---|------------|--------|-----------------|-----------------|
| 1 | RSI | 14 | > 70 | < 30 |
| 2 | MACD | 12/26/9 | MACD > Signal | MACD < Signal |
| 3 | Stochastic | 14 | > 80 | < 20 |
| 4 | CCI | 20 | > +100 | < −100 |
| 5 | Williams %R | 14 | > −20 | < −80 |
| 6 | MFI | 14 | > 80 | < 20 |
| 7 | Ultimate Oscillator | 7/14/28 | > 70 | < 30 |
| 8 | ATR | 14 | Волатильность | — |
| 9 | Bollinger Bands | 20/2 | Выше верхней | Ниже нижней |

### Детальное описание осцилляторов

**1. RSI (Relative Strength Index)**

Формула: `RSI = 100 - (100 / (1 + RS))`, где `RS = Средний прирост / Среднее падение`.

- `overbought` (> 70): возможна коррекция вниз
- `oversold` (< 30): возможен отскок вверх
- `neutral` (30–70): боковое движение

**2. MACD (Moving Average Convergence Divergence)**

Компоненты: MACD-линия, сигнальная линия, гистограмма. `MACD = EMA(12) - EMA(26)`, `Signal = EMA(9) от MACD`.

- `bullish`: MACD пересекает сигнальную линию снизу вверх
- `bearish`: MACD пересекает сигнальную линию сверху вниз

**3. Stochastic Oscillator**

`%K = 100 * (Close - Low_min) / (High_max - Low_min)`.

- `overbought` (> 80): цена у верхней границы
- `oversold` (< 20): цена у нижней границы

**4. CCI (Commodity Channel Index)**

`CCI = (Typical_Price - SMA) / (0.015 * Mean_Deviation)`.

- `overbought` (> +100): сильное отклонение вверх
- `oversold` (< −100): сильное отклонение вниз

**5. Williams %R**

`%R = (High_max - Close) / (High_max - Low_min) * (-100)`.

- `overbought` (> −20): цена около максимума
- `oversold` (< −80): цена около минимума

**6. MFI (Money Flow Index)**

Учитывает цену и объём. `MFI = 100 - (100 / (1 + Money_Ratio))`.

- `overbought` (> 80): перекуплен с учётом объёмов
- `oversold` (< 20): перепродан с учётом объёмов

**7. Ultimate Oscillator**

Периоды 7/14/28. Комбинирует три таймфрейма в один индикатор.

- `overbought` (> 70): перекуплен на всех таймфреймах
- `oversold` (< 30): перепродан на всех таймфреймах

**8. ATR (Average True Range)**

Измеряет волатильность. Не даёт сигналов покупки/продажи, используется для стоп-лоссов и оценки волатильности.

**9. Bollinger Bands**

`BB = SMA(20) ± 2 × Стандартное отклонение`.

- `above_upper`: цена выше верхней полосы (возможен откат)
- `below_lower`: цена ниже нижней полосы (возможен рост)
- `between`: цена в пределах полос

## 💾 База данных

### Таблица `kline_data` — OHLCV свечи

| Поле | Тип | Описание |
|------|-----|----------|
| `id` | SERIAL | PK |
| `symbol` | VARCHAR(20) | Торговая пара (`BTCUSDT`) |
| `open_time` | TIMESTAMP | Время открытия |
| `close_time` | TIMESTAMP | Время закрытия |
| `open_price` | FLOAT | Цена открытия |
| `high_price` | FLOAT | Максимум |
| `low_price` | FLOAT | Минимум |
| `close_price` | FLOAT | Цена закрытия |
| `volume` | FLOAT | Объём |
| `quote_volume` | FLOAT | Объём в котировочной валюте |
| `trades_count` | INTEGER | Кол-во сделок |
| `created_at` | TIMESTAMP | Время записи |

Индекс: `ix_kline_data_open_time`.

### Таблица `oscillator_data` — осцилляторы + скор

| Поле | Тип | Описание |
|------|-----|----------|
| `id` | SERIAL | PK |
| `kline_id` | INTEGER | Связь с `kline_data` |
| `symbol` | VARCHAR(20) | Торговая пара |
| `timestamp` | TIMESTAMP | Время расчёта |
| `rsi`, `rsi_signal` | FLOAT / VARCHAR | RSI и сигнал |
| `macd`, `macd_signal_line`, `macd_histogram`, `macd_signal` | FLOAT / VARCHAR | MACD |
| `stoch_k`, `stoch_d`, `stoch_signal` | FLOAT / VARCHAR | Stochastic |
| `cci`, `cci_signal` | FLOAT / VARCHAR | CCI |
| `williams_r`, `williams_r_signal` | FLOAT / VARCHAR | Williams %R |
| `mfi`, `mfi_signal` | FLOAT / VARCHAR | MFI |
| `ultimate_oscillator`, `uo_signal` | FLOAT / VARCHAR | Ultimate Oscillator |
| `atr` | FLOAT | ATR |
| `bb_upper`, `bb_middle`, `bb_lower`, `bb_position` | FLOAT / VARCHAR | Bollinger Bands |
| `overall_score` | FLOAT | Общий скор (−14…+14) |
| `overall_signal` | VARCHAR(20) | Общий сигнал |
| `created_at` | TIMESTAMP | Время записи |

Индексы: `ix_oscillator_data_kline_id`, `ix_oscillator_data_timestamp`. **UniqueConstraint на `kline_id` отсутствует** — при backfill проверяется существование перед вставкой.

### Таблица `derivatives_snapshots` — снимки деривативных метрик

| Поле | Тип | Описание |
|------|-----|----------|
| `id` | SERIAL | PK |
| `symbol`, `inst_id` | VARCHAR(20) / VARCHAR(30) | Внутренний / OKX-тикер |
| `timestamp` | TIMESTAMP | Время снимка (округлено к часу) |
| `funding_rate` | FLOAT | Ставка финансирования (доля, не %) |
| `open_interest_contracts` | FLOAT | OI в контрактах |
| `open_interest_usd` | FLOAT | OI в USD notional |
| `long_short_ratio` | FLOAT | Соотношение аккаунтов |
| `taker_buy_volume`, `taker_sell_volume` | FLOAT | Объёмы taker |
| `volume_usd` | FLOAT | Общий объём за период |
| `source` | VARCHAR(20) | `okx` |

**UniqueConstraint**: `uq_deriv_snapshot (symbol, timestamp, source)`.

### Таблица `funding_events` — история сеттлментов funding

| Поле | Тип | Описание |
|------|-----|----------|
| `id` | SERIAL | PK |
| `symbol`, `inst_id` | VARCHAR | Внутренний / OKX-тикер |
| `funding_time` | TIMESTAMP | Время сеттлмента |
| `realized_rate` | FLOAT | Реализованная ставка |
| `source` | VARCHAR(20) | `okx` |

**UniqueConstraint**: `uq_funding_event (symbol, funding_time, source)`.

### Таблица `liquidation_events` — история ликвидаций

| Поле | Тип | Описание |
|------|-----|----------|
| `id` | SERIAL | PK |
| `symbol`, `inst_id` | VARCHAR | Внутренний / OKX-тикер |
| `timestamp` | TIMESTAMP | Время ликвидации |
| `pos_side` | VARCHAR(10) | `long` / `short` (ликвидированная сторона) |
| `price` | FLOAT | Цена ликвидации |
| `size_contracts` | FLOAT | Объём в контрактах |
| `size_usd` | FLOAT | Notional в USD |

**UniqueConstraint**: `uq_liquidation_event (symbol, timestamp, price, size_contracts, pos_side)`.

### Полезные SQL-запросы

```sql
-- Количество сохранённых свечей
SELECT COUNT(*) FROM kline_data;

-- Последние 5 свечей
SELECT symbol, open_time, open_price, high_price, low_price, close_price, volume
FROM kline_data ORDER BY open_time DESC LIMIT 5;

-- Последний анализ осцилляторов
SELECT timestamp, overall_score, overall_signal, rsi, macd_signal, stoch_signal
FROM oscillator_data ORDER BY timestamp DESC LIMIT 1;

-- Текущие деривативные метрики (BTC)
SELECT symbol, timestamp, funding_rate, open_interest_usd, long_short_ratio
FROM derivatives_snapshots WHERE symbol = 'BTCUSDT'
ORDER BY timestamp DESC LIMIT 5;

-- Каскады ликвидаций за последний час
SELECT symbol, timestamp, pos_side, size_usd, price
FROM liquidation_events
WHERE timestamp > NOW() - INTERVAL '1 hour'
ORDER BY size_usd DESC LIMIT 10;

-- Баланс лонг/шорт ликвидаций за сутки
SELECT pos_side, COUNT(*) AS cnt, SUM(size_usd) AS total_usd
FROM liquidation_events
WHERE timestamp > NOW() - INTERVAL '1 day'
GROUP BY pos_side;
```

## 🌐 API Binance и OKX

### Binance (спот)

Используемый endpoint:

```
GET https://api.binance.com/api/v3/klines
```

| Параметр | Значение | Описание |
|----------|----------|----------|
| `symbol` | BTCUSDT | Торговая пара |
| `interval` | 1h | Интервал (1 час) |
| `limit` | 100 | Кол-во свечей |

Формат ответа:

```json
[
  [
    1499040000000,
    "0.01634790",
    "0.80000000",
    "0.01575800",
    "0.01577100",
    "148976.11427815",
    1499644799999,
    "2434.19055334",
    308,
    "1756.87402397",
    "28.46694368",
    "17928899.62484339"
  ]
]
```

### OKX V5 (спот + свопы)

Базовый URL: `https://www.okx.com/api/v5`

Для деривативов используются **публичные** эндпоинты — API-ключ не требуется:

| Метрика | Endpoint | Требует ключ |
|---------|----------|--------------|
| Funding Rate | `/public/funding-rate` | Нет |
| Open Interest | `/public/open-interest` | Нет |
| Long/Short Ratio | `/rubik/stat/contracts/long-short-account-ratio` | Нет |
| Taker Volume | `/rubik/stat/taker-volume-contract` | Нет |
| Funding History | `/public/funding-rate-history` | Нет |
| Liquidations | `/public/liquidation-orders` | Нет |

**Rate limits:**

- Public endpoints (`/public/*`): **20 req / 2 sec**
- Rubik statistics (`/rubik/*`): **5 req / 2 sec**

Сервис собирает данные последовательно (по одному запросу на инструмент), с интервалом 15 минут — с большим запасом укладывается в лимиты.

## 🔮 Деривативные метрики OKX

### Логика `sync_derivatives` (каждые 15 минут)

1. Если `DATA_SOURCE != okx` — пропуск
2. Для каждого инструмента:
   - Конвертация `okx` в `-SWAP` (если ещё не) — деривативы OKX доступны только для свопов
   - Снимок метрик (4 запроса: funding, OI, L/S ratio, taker volume) → `derivatives_snapshots` (UPSERT)
   - История funding (100 событий) → `funding_events` (INSERT … ON CONFLICT DO NOTHING)
   - Ликвидации (до 100 событий) → `liquidation_events` (INSERT … ON CONFLICT DO NOTHING)

**При старте сервиса** `sync_derivatives` вызывается **сразу**, не ждёт 15 минут.

### Металлы (XAU, XAG, XPT)

OKX предоставляет funding и ликвидации для металлических свопов. `open-interest` также работает. Если для какого-то инструмента эндпоинт вернёт 404, сервис залогирует `warning` и продолжит — остальные инструменты не пострадают.

### Что можно делать с деривативами

| Метрика | Диапазон | Интерпретация |
|---------|----------|---------------|
| `funding_rate` | ±0.0001 … ±0.001 | Положительный = лонги платят шортам (переполненность лонгов). Отрицательный = наоборот |
| `open_interest_usd` | миллионы $ | Рост OI + рост цены = новые деньги в лонги (продолжение тренда) |
| `long_short_ratio` | 0.5 … 6.0+ | Крайние значения (>3 или <0.7) — переполненность одной стороны, контр-трендовый сигнал |
| `taker_buy_volume / taker_sell_volume` | > 1.3 или < 0.7 | Доминирование одной стороны |
| Каскад ликвидаций | >$10M за 5 мин | Локальный экстремум, точка для отскока |

## 🤖 Telegram интеграция

### Настройка бота

1. Создание бота через `@BotFather`:
   ```
   /start
   /newbot
   Crypto Oscillator Analyzer
   crypto_oscillator_bot
   ```

2. Создание канала: добавьте бота администратором, скопируйте `@username`.

3. Настройка `.env`:
   ```
   TELEGRAM_BOT_TOKEN=123456789:ABCdefGHIjklMNOpqrsTUVwxyz
   TELEGRAM_CHANNEL_ID=@your_channel
   ```

### Формат сообщений

```
📊 ETH/USDT Анализ Осцилляторов
⏰ 2026-11-13 02:00 UTC
💰 Текущая цена: $3245.67

🟢 Общий сигнал: BUY
📈 Общий скорр балл: 7/14

━━━━━━━━━━━━━━━━━

📊 Детальный анализ осцилляторов:

1️⃣ RSI (14): 42.35
   Сигнал: ⚪️ Нейтральный

2️⃣ MACD: 12.45
   Сигнальная линия: 10.23
   Гистограмма: 2.22
   Сигнал: 🟢 Бычий
...
```

## 🎯 Система скоринга

### Принцип расчёта

Каждый осциллятор вносит вклад в общий скор:

| Балл | Значение |
|------|----------|
| +2 | Сильный сигнал на покупку (перепроданность) |
| +1 | Сигнал на покупку |
| 0 | Нейтральный сигнал |
| −1 | Сигнал на продажу |
| −2 | Сильный сигнал на продажу (перекупленность) |

### Веса осцилляторов

| Осциллятор | Вес |
|------------|-----|
| RSI | ±2 |
| MACD | ±1 |
| Stochastic | ±2 |
| CCI | ±1 |
| Williams %R | ±2 |
| MFI | ±2 |
| Ultimate Oscillator | ±2 |
| Bollinger Bands | ±2 |
| ATR | не участвует (волатильность) |

### Интерпретация общего скора

| Скор | Сигнал | Описание |
|------|--------|----------|
| +6 … +14 | `STRONG BUY` | Сильный сигнал на покупку |
| +3 … +5 | `BUY` | Сигнал на покупку |
| −2 … +2 | `NEUTRAL` | Нейтральный сигнал |
| −5 … −3 | `SELL` | Сигнал на продажу |
| −14 … −6 | `STRONG SELL` | Сильный сигнал на продажу |

## 🔧 Скрипты и утилиты

### `backfill_oscillators.py` — досчёт осцилляторов

Заполняет `oscillator_data` для свечей, у которых нет записи (после сбоя, рестарта, ручной загрузки истории).

```bash
# 1. Dry-run: показать план, ничего не писать
venv/bin/python backfill_oscillators.py --dry-run

# 2. Dry-run для одного символа
venv/bin/python backfill_oscillators.py --dry-run --symbol BTCUSDT

# 3. Реальный запуск (все символы, все свечи без осцилляторов)
venv/bin/python backfill_oscillators.py

# 4. Только первые N свечей (для теста)
venv/bin/python backfill_oscillators.py --limit 10
```

**Логика:**

1. Находит все `kline_data`, для которых нет `oscillator_data`
2. Для каждой берёт окно 100 свечей **до неё включительно**
3. Пропускает, если в окне < 28 свечей (недостаточно для RSI/MACD/UO)
4. Проверяет `exists(kline_id)` — **защита от дублей**
5. Считает через `oscillator_analyzer.analyze_all` — **тот же метод**, что в live-цикле
6. Сохраняет через `db.save_oscillator_data` — **тот же путь**, что в live-цикле

**Флаги:** `--dry-run`, `--symbol SYMBOL`, `--limit N`, `--batch N`.

### Диагностика/валидация backfill

Перед реальным запуском убедитесь, что пересчёт воспроизводит уже сохранённые значения:

```python
from database import db
from models import KlineData, OscillatorData
from sqlalchemy import select, desc
from oscillators import oscillator_analyzer

with db.get_session() as s:
    row = s.execute(
        select(OscillatorData, KlineData)
        .join(KlineData, OscillatorData.kline_id == KlineData.id)
        .where(KlineData.symbol == "BTCUSDT")
        .order_by(desc(KlineData.open_time))
        .limit(1)
    ).first()
    existing_osc, kline = row
    window = s.execute(
        select(KlineData).where(KlineData.symbol == "BTCUSDT")
        .where(KlineData.open_time <= kline.open_time)
        .order_by(KlineData.open_time.desc()).limit(100)
    ).scalars().all()
    window = list(reversed(window))
    dicts = [{'open_time': k.open_time, 'open': k.open_price, 'high': k.high_price,
              'low': k.low_price, 'close': k.close_price, 'volume': k.volume} for k in window]
    result = oscillator_analyzer.analyze_all(dicts)
    print(f"existing: {existing_osc.overall_score}/{existing_osc.overall_signal}")
    print(f"calc:     {result['overall_score']}/{result['overall_signal']}")
    print("MATCH" if result['overall_score'] == existing_osc.overall_score else "MISMATCH")
```

## 📝 Логирование

### Уровни

- **INFO**: нормальная работа
- **WARNING**: предупреждения (Telegram не настроен, недостаточно данных)
- **ERROR**: ошибки с полной трассировкой

### Расположение

```
crypto_analyzer.log   # файл логов
journalctl            # systemd (в production)
stdout                # консоль
```

### Пример логов

```
2026-11-13 02:00:00 - database - INFO - Сохранены данные осцилляторов для свечи 2126
2026-11-13 02:00:00 - telegram_sender - INFO - Сообщение успешно отправлено в Telegram
2026-11-13 02:00:00 - __main__ - INFO - [XAGUSDT] Анализ завершён: BUY (3/14)
2026-11-13 02:15:00 - database - INFO - Сохранён derivatives snapshot для BTCUSDT
2026-11-13 02:15:01 - database - INFO - Сохранено 100 funding events для BTCUSDT
2026-11-13 02:15:02 - database - INFO - Сохранено 100 liquidation events для BTCUSDT
2026-11-13 02:15:03 - __main__ - INFO - Синхронизация деривативов завершена
```

### Мониторинг

```bash
# Просмотр логов в реальном времени
tail -f crypto_analyzer.log

# Фильтрация ошибок
grep ERROR crypto_analyzer.log

# Последние 50 строк
tail -n 50 crypto_analyzer.log
```

## 🔒 Безопасность

- **Никогда не коммитьте `.env`**: `echo ".env" >> .gitignore`
- **Сильные пароли для БД**
- **Ограничьте доступ к серверу**: PostgreSQL `listen_addresses = 'localhost'`
- **Регулярно обновляйте зависимости**: `pip list --outdated`
- **Виртуальное окружение**: `python -m venv venv`
- **API-ключи OKX не требуются** — все используемые эндпоинты публичные

```bash
# Проверка уязвимостей
pip install safety
safety check

# Статический анализ
pip install bandit
bandit -r .
```

## 🔧 Решение проблем

### `AttributeError: 'Query' object has no attribute 'unique'`

**Причина:** старая версия кода + SQLAlchemy 2.0. `Query.unique()` / `Query.distinct(column)` удалены в 2.0. `get_last_klines` переписан на `select()` + `session.execute().scalars().all()`. Проверьте, что в `database.py` нет `.unique()` / `.distinct(column)` на `Query`.

### `NameError: name 'klines' is not defined`

**Причина:** несовпадение имени переменной в `get_last_klines` (`result` вместо `klines`). Проверьте:

```python
klines = session.execute(stmt).scalars().all()
for k in reversed(klines):
    ...
```

### `ProgrammingError: no unique or exclusion constraint matching ON CONFLICT`

**Причина:** `UniqueConstraint` не объявлен в модели или БД создана до фикса. Пересоздать таблицы:

```bash
venv/bin/python -c "
from database import db
from sqlalchemy import text
with db.engine.begin() as conn:
    conn.execute(text('DROP TABLE IF EXISTS derivatives_snapshots CASCADE'))
    conn.execute(text('DROP TABLE IF EXISTS funding_events CASCADE'))
    conn.execute(text('DROP TABLE IF EXISTS liquidation_events CASCADE'))
db.create_tables()
"
```

### `IndentationError` после ручной правки

**Причина:** метод вставлен не туда (например, после `db = Database()`). Проверьте:

```bash
grep -n "db = Database()" database.py
```

Все `def` внутри класса должны быть **до** этой строки.

### OKX возвращает 404 на деривативы

`perp-metrics` — эндпоинт **стороннего шлюза**, не OKX. В коде используются **нативные** OKX-эндпоинты: `funding-rate`, `open-interest`, `long-short-account-ratio`, `taker-volume-contract`, `funding-rate-history`, `liquidation-orders`. Проверить доступность:

```bash
curl -s "https://www.okx.com/api/v5/public/funding-rate?instId=BTC-USDT-SWAP" | python3 -m json.tool | head -10
```

### Пустые скоры в исторических свечах

**Причина:** `process_update` считает только для последней свечи. Промежуточные свечи остаются без `oscillator_data`. Решение:

```bash
venv/bin/python backfill_oscillators.py --dry-run
venv/bin/python backfill_oscillators.py
```

### Rate limit `429 Too Many Requests`

**Причина:** слишком частые запросы к OKX. Проверьте `DERIVATIVES_SYNC_INTERVAL_MIN` (минимум 15) и `FUNDING_HISTORY_LIMIT` (максимум 100).

### Ошибка подключения к PostgreSQL

```
Error: could not connect to server: Connection refused
```

```bash
# macOS
brew services list | grep postgresql
brew services start postgresql@15

# Linux
sudo systemctl status postgresql
sudo systemctl start postgresql
```

### Ошибка аутентификации БД

```
Error: password authentication failed for user "postgres"
```

```bash
sudo -u postgres psql
ALTER USER postgres PASSWORD 'new_password';
```

### Недостаточно данных для расчёта

```
WARNING - Недостаточно данных для расчёта: 14 свечей
```

Подождите накопления (минимум **28 свечей**).

### Ошибка отправки в Telegram

Проверьте:
- Правильность токена
- Бот добавлен администратором канала
- Правильный `@username` или ID канала

### Диагностика

```bash
# Полная диагностика
python main.py --test

# Проверка БД
psql -d crypto_analyzer -c "\dt"
psql -d crypto_analyzer -c "SELECT COUNT(*) FROM kline_data;"

# Проверка Binance
curl "https://api.binance.com/api/v3/klines?symbol=ETHUSDT&interval=1h&limit=1"

# Проверка OKX
curl "https://www.okx.com/api/v5/public/funding-rate?instId=BTC-USDT-SWAP"

# Проверка Telegram
curl "https://api.telegram.org/bot<YOUR_TOKEN>/getMe"
```

## 👨‍💻 Разработка

### Добавление нового осциллятора

1. Добавьте метод в `oscillators.py`:
   ```python
   def calculate_new_oscillator(self, data):
       return value, signal
   ```
2. Добавьте поле в `OscillatorData` в `models.py`:
   ```python
   new_oscillator = Column(Float, nullable=True)
   new_oscillator_signal = Column(String(20), nullable=True)
   ```
3. Обновите `calculate_overall_score()`
4. Добавьте в `_filter_oscillator_fields()` в `main.py`

### Добавление нового источника данных

1. Реализуйте `MarketDataClient` (см. `clients/okx_client.py`)
2. Зарегистрируйте в `clients/factory.py`
3. Добавьте в `DATA_SOURCE` в конфиге

### Изменение торговой пары

`INSTRUMENTS` в `config.py`:

```python
{"id": "BTCUSDT", "okx": "BTC-USDT", "okx_type": "SPOT", "binance": "BTCUSDT"}
```

Для деривативов `okx` автоматически конвертируется в `BTC-USDT-SWAP`.

### Добавление новых интервалов

```python
INTERVAL = os.getenv('INTERVAL', '1h')  # 1h, 4h, 1d, 1w
```

## 📈 Производительность

| Метрика | Значение | Примечание |
|---------|----------|------------|
| Время основного цикла | ~2–5 сек | 13 инструментов |
| Время `sync_derivatives` | ~10–15 сек | 13 × 6 запросов к OKX |
| Нагрузка на API Binance | 1 запрос/час | Лимит: 1200/мин |
| Нагрузка на API OKX | ~78 запросов/15 мин | Лимит: 5–20/2 сек |
| Размер БД | ~15–30 МБ/месяц | С деривативами |
| Память | ~60–100 МБ RAM | Всё приложение |

## 📝 Changelog

### v1.1.0 (2026-11-13)

- ✨ **Pluggable data sources**: Binance ↔ OKX через `DATA_SOURCE`
- ✨ **Деривативные метрики OKX**: funding rate, open interest, long/short ratio, taker volume
- ✨ **Ликвидации OKX**: история событий с разбивкой long/short
- ✨ **`backfill_oscillators.py`** — скрипт досчёта осцилляторов для исторических свечей
- 🔧 **Миграция на SQLAlchemy 2.0**: `select()` + `session.execute()`
- 🔧 **Автодогон истории**: `process_update` догоняет все пропущенные свечи
- 🔧 **Автозапуск `sync_derivatives`** при старте сервиса
- 🐛 **Fix**: `NameError: name 'klines' is not defined` в `get_last_klines`
- 🐛 **Fix**: `IndentationError` при добавлении методов в `database.py`
- 📝 **Документация**: полный README с деривативами и troubleshooting

### v1.0.0 (2026-04-28)

- ✨ Первый релиз
- 📊 9 технических осцилляторов
- 💾 PostgreSQL интеграция
- 🤖 Telegram бот
- 🎯 Система скоринга
- 🐳 Docker поддержка

## 📄 Лицензия

MIT License

Copyright (c) 2026 Crypto Oscillator Analyzer

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

---

## ⚠️ Дисклеймер

Данный инструмент предоставляется исключительно в информационных целях. Торговые сигналы не являются инвестиционными рекомендациями. Всегда проводите собственный анализ перед принятием торговых решений.

Криптовалюты являются высокорискованными активами. Торговля криптовалютами может привести к потере всех инвестированных средств.

