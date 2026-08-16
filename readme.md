# 🔮 Crypto Oscillator Analyzer

Профессиональный анализатор криптовалютного рынка с расчетом технических осцилляторов и автоматической отправкой сигналов в Telegram.

[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://www.python.org/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-15-blue.svg)](https://www.postgresql.org/)
[![Binance](https://img.shields.io/badge/Binance-API-yellow.svg)](https://www.binance.com/)
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
- [API Binance](#-api-binance)
- [Telegram интеграция](#-telegram-интеграция)
- [Система скоринга](#-система-скоринга)
- [Логирование](#-логирование)
- [Безопасность](#-безопасность)
- [Решение проблем](#-решение-проблем)
- [Разработка](#-разработка)
- [Лицензия](#-лицензия)

## 🚀 Возможности

- 📊 **Автоматический сбор данных** с Binance API каждый час
- 💾 **Сохранение истории** в PostgreSQL (свечи + осцилляторы)
- 📈 **Расчет 9 технических осцилляторов**
- 🎯 **Скоринговая система** (-14 до +14 баллов)
- 🤖 **Telegram бот** для автоматических уведомлений
- 📝 **Подробное логирование** всех операций
- 🔄 **Умная проверка** - не запрашивает данные, если они актуальны
- 🐳 **Docker поддержка** для PostgreSQL

## 🏗 Архитектура проекта

### Структура файлов

| Файл | Назначение | Ключевые компоненты |
|------|------------|---------------------|
| `config.py` | Конфигурация приложения | Настройки БД, Telegram, Binance API, интервалы обновления |
| `database.py` | Работа с PostgreSQL | Подключение к БД, CRUD операции, создание таблиц, сессии |
| `models.py` | SQLAlchemy модели | KlineData (свечи), OscillatorData (осцилляторы) |
| `binance_client.py` | Клиент Binance API | Запросы к API, получение исторических свечей |
| `oscillators.py` | Расчет осцилляторов | RSI, MACD, Stochastic, CCI, Williams %R, MFI, UO, ATR, BB |
| `telegram_sender.py` | Отправка в Telegram | Форматирование сообщений, отправка в канал |
| `main.py` | Главный файл приложения | Планировщик, оркестрация, CLI аргументы |
| `requirements.txt` | Зависимости Python | Список всех необходимых пакетов |
| `.env.example` | Пример конфигурации | Шаблон переменных окружения |
| `docker-compose.yml` | Docker для PostgreSQL | Контейнер с PostgreSQL 15 |
| `README.md` | Документация | Полное описание проекта |

### Детальное описание модулей

| Модуль | Классы | Основные методы | Зависимости |
|--------|--------|-----------------|-------------|
| `config.py` | `Config` | `database_url` (property) | python-dotenv |
| `database.py` | `Database` | `create_tables()`, `get_session()`, `save_kline_data()`, `save_oscillator_data()`, `get_last_klines()`, `get_latest_kline_id()` | SQLAlchemy, models |
| `models.py` | `KlineData`, `OscillatorData` | SQLAlchemy модели (наследуют `Base`) | SQLAlchemy |
| `binance_client.py` | `BinanceClient` | `fetch_klines(limit)` | requests |
| `oscillators.py` | `OscillatorAnalyzer` | `analyze_all()`, `calculate_rsi()`, `calculate_macd()`, `calculate_stochastic()`, `calculate_cci()`, `calculate_williams_r()`, `calculate_mfi()`, `calculate_ultimate_oscillator()`, `calculate_atr()`, `calculate_bollinger_bands()`, `calculate_overall_score()` | numpy, pandas |
| `telegram_sender.py` | `TelegramSender` | `send_message()`, `format_message()`, `_format_signal()` | requests |
| `main.py` | `CryptoAnalyzerApp` | `initialize()`, `process_update()`, `get_latest_kline()`, `run_once()`, `start_scheduler()`, `_filter_oscillator_fields()` | Все модули |

### Поток данных между модулями

| Шаг | Модуль | Действие | Входные данные | Выходные данные |
|-----|--------|----------|----------------|-----------------|
| 1 | `main.py` | Запуск таймера | Интервал из `config.py` | Сигнал к обновлению |
| 2 | `binance_client.py` | Запрос к API | SYMBOL, INTERVAL, LIMIT | Список свечей (JSON) |
| 3 | `database.py` | Сохранение в БД | Список свечей | ID записей |
| 4 | `database.py` | Чтение из БД | LIMIT=100 | 100 последних свечей |
| 5 | `oscillators.py` | Расчет осцилляторов | Свечи (100 шт.) | Словарь с 9 осцилляторами |
| 6 | `database.py` | Сохранение осцилляторов | Словарь осцилляторов | ID записи |
| 7 | `oscillators.py` | Расчет общего скора | Словарь осцилляторов | Score + Signal |
| 8 | `telegram_sender.py` | Отправка сообщения | Результаты анализа | Сообщение в Telegram |

### Переменные окружения (.env)

| Переменная | По умолчанию | Описание | Обязательная |
|------------|--------------|----------|--------------|
| `DB_HOST` | localhost | Хост PostgreSQL | Да |
| `DB_PORT` | 5432 | Порт PostgreSQL | Да |
| `DB_NAME` | crypto_analyzer | Имя базы данных | Да |
| `DB_USER` | postgres | Пользователь БД | Да |
| `DB_PASSWORD` | (пусто) | Пароль БД | Да |
| `TELEGRAM_BOT_TOKEN` | (пусто) | Токен Telegram бота | Нет* |
| `TELEGRAM_CHANNEL_ID` | (пусто) | ID/username канала | Нет* |
| `UPDATE_INTERVAL_HOURS` | 1 | Интервал обновления | Да |

*Telegram настройки не обязательны для тестового режима

### Константы и параметры

| Параметр | Значение | Файл | Описание |
|----------|----------|------|----------|
| `SYMBOL` | ETHUSDT | config.py | Торговая пара |
| `INTERVAL` | 1h | config.py | Интервал свечей |
| `BINANCE_API_URL` | api.binance.com/api/v3/klines | config.py | URL Binance API |
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

## 🔄 Поток данных

### Основной цикл работы

| Шаг | Этап | Модуль | Описание | Входные данные | Выходные данные | Время выполнения |
|-----|------|--------|----------|----------------|-----------------|------------------|
| 1 | ⏰ **Таймер** | `main.py` | Срабатывает каждый час | Интервал из `config.py` | Сигнал к запуску | ~0 сек |
| 2 | 🌐 **Запрос к API** | `binance_client.py` | GET запрос к Binance API | SYMBOL, INTERVAL, LIMIT | JSON с данными свечей | ~0.5-1 сек |
| 3 | 💾 **Сохранение свечей** | `database.py` | Запись в таблицу `kline_data` | Данные свечей из API | ID новых записей | ~0.1-0.3 сек |
| 4 | 📊 **Расчет осцилляторов** | `oscillators.py` | Расчет 9 осцилляторов | 100 последних свечей из БД | Словарь со значениями | ~0.5-1 сек |
| 5 | 💾 **Сохранение результатов** | `database.py` | Запись в таблицу `oscillator_data` | Данные осцилляторов | ID записи | ~0.1 сек |
| 6 | 🎯 **Формирование сигнала** | `oscillators.py` | Расчет общего скора (-14 до +14) | Значения осцилляторов | Сигнал (BUY/SELL/NEUTRAL) | ~0.1 сек |
| 7 | 📨 **Отправка в Telegram** | `telegram_sender.py` | Форматирование и отправка | Все результаты анализа | Сообщение в канал | ~0.5-1 сек |

### Детализация каждого шага

| Шаг | API / Функция | Параметры | Пример запроса / Код | Пример ответа |
|-----|---------------|-----------|---------------------|---------------|
| 1 | `schedule.every(1).hours.do()` | `UPDATE_INTERVAL_HOURS=1` | `schedule.every(1).hours.do(process_update)` | Запуск `process_update()` |
| 2 | `GET /api/v3/klines` | `symbol=ETHUSDT`<br>`interval=1h`<br>`limit=1` | `https://api.binance.com/api/v3/klines?symbol=ETHUSDT&interval=1h&limit=1` | `[[1499040000000, "0.01634790", ...]]` |
| 3 | `save_kline_data()` | `kline_list` - список свечей | `db.save_kline_data(klines)` | `INFO: Сохранена свеча за 2026-04-28 20:00:00` |
| 4 | `analyze_all()` | `klines_data` - 100 свечей | `oscillator_analyzer.analyze_all(klines_from_db)` | `{rsi: 45.23, macd: 2.15, ...}` |
| 5 | `save_oscillator_data()` | `osc_data` - словарь осцилляторов | `db.save_oscillator_data(oscillator_fields, latest_kline_id)` | `INFO: Сохранены данные осцилляторов для свечи 123` |
| 6 | `calculate_overall_score()` | `oscillator_data` - значения осцилляторов | `score = oscillator_analyzer.calculate_overall_score(result)` | `{score: 7, signal: "BUY"}` |
| 7 | `send_message()` | `data` - полный анализ | `telegram_sender.send_message(analysis_result)` | `INFO: Сообщение успешно отправлено в Telegram` |

### Визуальная схема потока данных

| Откуда | → | Куда | Тип данных | Формат |
|--------|---|------|------------|--------|
| **Binance API** | → | `binance_client.py` | HTTP Response | JSON Array |
| `binance_client.py` | → | `database.py` | Список словарей | `[{open_time, open, high, low, close, volume, ...}]` |
| `database.py` | → | **PostgreSQL** (`kline_data`) | SQL INSERT | Строки таблицы |
| **PostgreSQL** (`kline_data`) | → | `oscillators.py` | SQL SELECT | 100 последних свечей |
| `oscillators.py` | → | `database.py` | Словарь значений | `{rsi: float, macd: float, ...}` |
| `database.py` | → | **PostgreSQL** (`oscillator_data`) | SQL INSERT | Строка таблицы |
| `oscillators.py` | → | `telegram_sender.py` | Словарь с сигналом | `{overall_score: int, overall_signal: str, ...}` |
| `telegram_sender.py` | → | **Telegram API** | HTTP POST | Markdown сообщение |

### Статистика выполнения

| Метрика | Значение | Примечание |
|---------|----------|------------|
| Общее время цикла | ~2-5 секунд | Зависит от сети и нагрузки |
| Задержка API Binance | ~0.5-1 сек | Может варьироваться |
| Время расчета осцилляторов | ~0.5-1 сек | Для 100 свечей |
| Время сохранения в БД | ~0.2-0.5 сек | Два INSERT запроса |
| Отправка в Telegram | ~0.5-1 сек | Сетевая задержка |
| Нагрузка на CPU | Минимальная | ~5-10% на расчетах |
| Использование RAM | ~50-100 МБ | Все приложение |

### Обработка ошибок на каждом шаге

| Шаг | Возможная ошибка | Обработка | Действие |
|-----|------------------|-----------|----------|
| 1 | Таймер не запустился | `try/except` в `start_scheduler()` | Логирование, повторная попытка |
| 2 | Сетевая ошибка / API недоступен | `try/except` в `fetch_klines()` | Логирование ERROR, пропуск цикла |
| 3 | Ошибка записи в БД | `try/except` в `save_kline_data()` | Логирование, rollback транзакции |
| 4 | Недостаточно данных (< 28 свечей) | Проверка `len(klines) < 28` | WARNING, пропуск анализа |
| 5 | Ошибка сохранения осцилляторов | `try/except` в `save_oscillator_data()` | Логирование, rollback |
| 6 | Ошибка в расчете скора | `try/except` в `calculate_overall_score()` | Возврат нейтрального сигнала |
| 7 | Ошибка отправки в Telegram | `try/except` в `send_message()` | Логирование WARNING (не критично) |

### 📦 Описание модулей

| Модуль | Назначение | Ключевые функции |
|--------|------------|------------------|
| `config.py` | Управление настройками | Загрузка .env, параметры БД и API |
| `database.py` | Работа с PostgreSQL | CRUD операции, создание таблиц |
| `models.py` | Модели данных | KlineData, OscillatorData |
| `binance_client.py` | API интеграция | Получение свечей с Binance |
| `oscillators.py` | Технический анализ | Расчет RSI, MACD, Stochastic и др. |
| `telegram_sender.py` | Уведомления | Форматирование и отправка в Telegram |
| `main.py` | Оркестратор | Планировщик, координация всех модулей |

## 🛠 Технический стек

| Технология | Версия | Назначение |
|------------|--------|------------|
| Python | 3.8+ | Основной язык программирования |
| PostgreSQL | 15 | Реляционная база данных |
| SQLAlchemy | 2.0+ | ORM для работы с БД |
| psycopg2-binary | 2.9+ | PostgreSQL драйвер |
| Requests | 2.31+ | HTTP запросы к API |
| Pandas | 2.1+ | Обработка и анализ данных |
| NumPy | 1.26+ | Математические вычисления |
| Schedule | 1.2+ | Планировщик задач |
| python-dotenv | 1.0+ | Переменные окружения |

## 📦 Установка и настройка

### Предварительные требования

- Python 3.8 или выше
- PostgreSQL 15 или Docker
- Git
- Telegram Bot Token (опционально)

### Шаг 1: Клонирование репозитория

```bash
git clone <your-repo-url>
cd crypto_analyzer
```
Шаг 2: Установка зависимостей
```bash
pip install -r requirements.txt
```
Шаг 3: Настройка базы данных
Вариант А: Локальный PostgreSQL
```bash
# macOS
brew install postgresql@15
brew services start postgresql@15
createdb crypto_analyzer

# Linux (Ubuntu/Debian)
sudo apt install postgresql postgresql-contrib
sudo systemctl start postgresql
sudo -u postgres createdb crypto_analyzer

# Windows
# Скачайте и установите PostgreSQL с официального сайта
# Создайте базу данных через pgAdmin или psql
```
Вариант Б: Docker
```bash
docker-compose up -d

# Проверка
docker ps
docker logs crypto_analyzer_db
```
Шаг 4: Конфигурация
```bash
# Копирование примера конфигурации
cp .env.example .env

# Редактирование настроек
nano .env
Пример .env файла:

```
# Настройки базы данных PostgreSQL
DB_HOST=localhost
DB_PORT=5432
DB_NAME=crypto_analyzer
DB_USER=postgres
DB_PASSWORD=your_password_here

# Настройки Telegram
TELEGRAM_BOT_TOKEN=123456789:ABCdefGHIjklMNOpqrsTUVwxyz
TELEGRAM_CHANNEL_ID=@your_channel_username

# Настройки приложения
UPDATE_INTERVAL_HOURS=1
Шаг 5: Проверка установки
bash
# Проверка подключения к БД
psql -h localhost -U postgres -d crypto_analyzer -c "\conninfo"

# Тестовый запуск
python main.py --test


## 🚀 Использование
Режимы запуска
```bash
# Запуск планировщика (обновление каждый час)
python main.py

# Однократное выполнение
python main.py --once
```
# Тестовый запуск (вывод в консоль, без Telegram)
```
python main.py --test
```

Демонизация (Linux/macOS)
Использование systemd (Linux)
Создайте файл /etc/systemd/system/crypto-analyzer.service:
```
ini
[Unit]
Description=Crypto Oscillator Analyzer
After=network.target postgresql.service

[Service]
Type=simple
User=your_user
WorkingDirectory=/path/to/crypto_analyzer
ExecStart=/usr/bin/python3 main.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
bash
sudo systemctl daemon-reload
sudo systemctl enable crypto-analyzer
sudo systemctl start crypto-analyzer
sudo systemctl status crypto-analyzer
Использование launchd (macOS)
Создайте файл ~/Library/LaunchAgents/com.crypto.analyzer.plist:

xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.crypto.analyzer</string>
    <key>ProgramArguments</key>
    <array>
        <string>/usr/bin/python3</string>
        <string>/path/to/crypto_analyzer/main.py</string>
    </array>
    <key>WorkingDirectory</key>
    <string>/path/to/crypto_analyzer</string>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <true/>
    <key>StandardOutPath</key>
    <string>/path/to/crypto_analyzer/stdout.log</string>
    <key>StandardErrorPath</key>
    <string>/path/to/crypto_analyzer/stderr.log</string>
</dict>
</plist>
```
---
```bash
launchctl load ~/Library/LaunchAgents/com.crypto.analyzer.plist
launchctl start com.crypto.analyzer
```
📊 Осцилляторы и сигналы
Список рассчитываемых осцилляторов
№	Осциллятор	Период	Сигнал перекупленности	Сигнал перепроданности
1	RSI	14	> 70	< 30
2	MACD	12/26/9	MACD > Signal	MACD < Signal
3	Stochastic	14	> 80	< 20
4	CCI	20	> +100	< -100
5	Williams %R	14	> -20	< -80
6	MFI	14	> 80	< 20
7	Ultimate Oscillator	7/14/28	> 70	< 30
8	ATR	14	Волатильность	-
9	Bollinger Bands	20/2	Выше верхней	Ниже нижней

### Детальное описание осцилляторов
1. RSI (Relative Strength Index)
Формула: RSI = 100 - (100 / (1 + RS)), где RS = Средний прирост / Среднее падение

Интерпретация: Показывает силу тренда и потенциальные точки разворота

Сигналы:

overbought (> 70): Возможна коррекция вниз

oversold (< 30): Возможен отскок вверх

neutral (30-70): Боковое движение

2. MACD (Moving Average Convergence Divergence)
Компоненты: MACD линия, Сигнальная линия, Гистограмма

Формула: MACD = EMA(12) - EMA(26), Signal = EMA(9) от MACD

Сигналы:

bullish: MACD пересекает сигнальную линию снизу вверх

bearish: MACD пересекает сигнальную линию сверху вниз

3. Stochastic Oscillator
Формула: %K = 100 * (Close - Low_min) / (High_max - Low_min)

Сигналы:

overbought (> 80): Цена у верхней границы диапазона

oversold (< 20): Цена у нижней границы диапазона

4. CCI (Commodity Channel Index)
Формула: CCI = (Typical_Price - SMA) / (0.015 * Mean_Deviation)

Сигналы:

overbought (> +100): Сильное отклонение вверх

oversold (< -100): Сильное отклонение вниз

5. Williams %R
Формула: %R = (High_max - Close) / (High_max - Low_min) * (-100)

Сигналы:

overbought (> -20): Цена около максимума

oversold (< -80): Цена около минимума

6. MFI (Money Flow Index)
Учитывает: Цену и объем торгов

Формула: MFI = 100 - (100 / (1 + Money_Ratio))

Сигналы:

overbought (> 80): Перекуплен с учетом объемов

oversold (< 20): Перепродан с учетом объемов

7. Ultimate Oscillator
Периоды: Краткосрочный (7), среднесрочный (14), долгосрочный (28)

Сигналы:

overbought (> 70): Перекуплен на всех таймфреймах

oversold (< 30): Перепродан на всех таймфреймах

8. ATR (Average True Range)
Назначение: Измерение волатильности рынка

Не дает сигналов: покупки/продажи

Использование: Установка стоп-лоссов, оценка волатильности

9. Bollinger Bands
Компоненты: Верхняя, средняя, нижняя полосы

Формула: BB = SMA(20) ± 2 × Стандартное отклонение

Сигналы:

above_upper: Цена выше верхней полосы (возможен откат)

below_lower: Цена ниже нижней полосы (возможен рост)

between: Цена в пределах полос (нормальное движение)

💾 База данных
Структура таблиц
Таблица kline_data
Хранит исторические данные свечей с Binance.

Поле	Тип	Описание
id	SERIAL	Уникальный идентификатор
symbol	VARCHAR(20)	Торговая пара (ETHUSDT)
open_time	TIMESTAMP	Время открытия свечи
close_time	TIMESTAMP	Время закрытия свечи
open_price	FLOAT	Цена открытия
high_price	FLOAT	Максимальная цена
low_price	FLOAT	Минимальная цена
close_price	FLOAT	Цена закрытия
volume	FLOAT	Объем торгов
quote_volume	FLOAT	Объем в котировочной валюте
trades_count	INTEGER	Количество сделок
created_at	TIMESTAMP	Время записи в БД
Таблица oscillator_data
Хранит рассчитанные значения осцилляторов и сигналы.

Поле	Тип	Описание
id	SERIAL	Уникальный идентификатор
kline_id	INTEGER	Связь с kline_data
symbol	VARCHAR(20)	Торговая пара
timestamp	TIMESTAMP	Время расчета
rsi	FLOAT	Значение RSI
rsi_signal	VARCHAR(20)	Сигнал RSI
macd	FLOAT	Значение MACD
macd_signal_line	FLOAT	Сигнальная линия
macd_histogram	FLOAT	Гистограмма MACD
macd_signal	VARCHAR(20)	Сигнал MACD
stoch_k	FLOAT	Stochastic %K
stoch_d	FLOAT	Stochastic %D
stoch_signal	VARCHAR(20)	Сигнал Stochastic
cci	FLOAT	Значение CCI
cci_signal	VARCHAR(20)	Сигнал CCI
williams_r	FLOAT	Williams %R
williams_r_signal	VARCHAR(20)	Сигнал Williams %R
mfi	FLOAT	Money Flow Index
mfi_signal	VARCHAR(20)	Сигнал MFI
ultimate_oscillator	FLOAT	Ultimate Oscillator
uo_signal	VARCHAR(20)	Сигнал UO
atr	FLOAT	Average True Range
bb_upper	FLOAT	Верхняя полоса BB
bb_middle	FLOAT	Средняя полоса BB
bb_lower	FLOAT	Нижняя полоса BB
bb_position	VARCHAR(20)	Позиция цены в BB
overall_score	FLOAT	Общий скор (от -14 до +14)
overall_signal	VARCHAR(20)	Общий сигнал
created_at	TIMESTAMP	Время записи
Полезные SQL запросы
sql
-- Количество сохраненных свечей
SELECT COUNT(*) FROM kline_data;

-- Последние 5 свечей
SELECT symbol, open_time, open_price, high_price, low_price, close_price, volume
FROM kline_data 
ORDER BY open_time DESC 
LIMIT 5;

-- Последний анализ осцилляторов
SELECT timestamp, overall_score, overall_signal, rsi, macd_signal, stoch_signal
FROM oscillator_data 
ORDER BY timestamp DESC 
LIMIT 1;

-- История сигналов
SELECT 
    timestamp,
    overall_signal,
    overall_score,
    rsi,
    rsi_signal,
    macd_signal,
    stoch_signal
FROM oscillator_data 
ORDER BY timestamp DESC 
LIMIT 10;

-- Статистика сигналов
SELECT 
    overall_signal, 
    COUNT(*) as count,
    AVG(overall_score) as avg_score
FROM oscillator_data 
GROUP BY overall_signal 
ORDER BY count DESC;
🌐 API Binance
Используемый endpoint
text
GET https://api.binance.com/api/v3/klines
Параметры запроса
Параметр	Значение	Описание
symbol	ETHUSDT	Торговая пара
interval	1h	Интервал свечей (1 час)
limit	100	Количество свечей
Формат ответа
json
[
  [
    1499040000000,      // Время открытия
    "0.01634790",       // Цена открытия
    "0.80000000",       // Максимальная цена
    "0.01575800",       // Минимальная цена
    "0.01577100",       // Цена закрытия
    "148976.11427815",  // Объем
    1499644799999,      // Время закрытия
    "2434.19055334",    // Объем в котировочной валюте
    308,                // Количество сделок
    "1756.87402397",    // Объем тейкера
    "28.46694368",      // Объем тейкера в котировочной валюте
    "17928899.62484339" // Игнорируется
  ]
]
Обработка ошибок API
Сетевые ошибки: Автоматическое логирование и повторная попытка

Лимиты API: Binance разрешает 1200 запросов в минуту (мы делаем 1 в час)

Неверные данные: Проверка длины и типов данных перед сохранением

🤖 Telegram интеграция
Настройка бота
Создание бота через @BotFather:

text
/start
/newbot
Crypto Oscillator Analyzer
crypto_oscillator_bot
# Получите токен: 123456789:ABCdefGHIjklMNOpqrsTUVwxyz
Создание канала:

Создайте публичный или приватный канал

Добавьте бота как администратора

Скопируйте username канала (@your_channel)

Настройка .env:

env
TELEGRAM_BOT_TOKEN=123456789:ABCdefGHIjklMNOpqrsTUVwxyz
TELEGRAM_CHANNEL_ID=@your_channel
Формат сообщений
Сообщение содержит:

📊 Заголовок с торговой парой

⏰ Время анализа

💰 Текущая цена ETH/USDT

🎯 Общий сигнал (STRONG BUY/BUY/NEUTRAL/SELL/STRONG SELL)

📈 Общий скорр балл (-14 до +14)

📋 Детальный анализ всех 9 осцилляторов

📊 Расшифровка скора по каждому осциллятору

⚠️ Дисклеймер

Пример сообщения:

text
📊 ETH/USDT Анализ Осцилляторов
⏰ 2026-04-28 20:00 UTC
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
🎯 Система скоринга
Принцип расчета
Каждый осциллятор вносит вклад в общий скор:

Балл	Значение
+2	Сильный сигнал на покупку (перепроданность)
+1	Сигнал на покупку
0	Нейтральный сигнал
-1	Сигнал на продажу
-2	Сильный сигнал на продажу (перекупленность)
Веса осцилляторов
Осциллятор	Вес	Сильный сигнал	Слабый сигнал
RSI	±2	overbought/oversold	-
MACD	±1	bullish/bearish	-
Stochastic	±2	overbought/oversold	-
CCI	±1	overbought/oversold	-
Williams %R	±2	overbought/oversold	-
MFI	±2	overbought/oversold	-
Ultimate Oscillator	±2	overbought/oversold	-
Bollinger Bands	±2	above_upper/below_lower	-
ATR не участвует в скоринге (используется для оценки волатильности)

Интерпретация общего скора
Скор	Сигнал	Эмодзи	Описание
+6 до +14	STRONG BUY	🟢🟢	Сильный сигнал на покупку
+3 до +5	BUY	🟢	Сигнал на покупку
-2 до +2	NEUTRAL	⚪️	Нейтральный сигнал
-5 до -3	SELL	🔴	Сигнал на продажу
-14 до -6	STRONG SELL	🔴🔴	Сильный сигнал на продажу
Пример расчета
text
RSI (42.35):        neutral → 0 баллов
MACD:               bullish → +1 балл
Stochastic (35.2):  neutral → 0 баллов
CCI (-45.3):        neutral → 0 баллов
Williams %R (-35):  neutral → 0 баллов
MFI (15.8):         oversold → +2 балла
Ultimate Osc (25):  oversold → +2 балла
Bollinger Bands:    below_lower → +2 балла

Общий скор: +7/14 → BUY
📝 Логирование
Уровни логирования
INFO: Нормальная работа приложения

WARNING: Предупреждения (например, Telegram не настроен)

ERROR: Ошибки с полной трассировкой

Расположение логов
text
crypto_analyzer.log    # Файл логов
stdout                 # Консольный вывод
Пример логов
text
2026-04-28 20:00:00,123 - __main__ - INFO - ==================================================
2026-04-28 20:00:00,124 - __main__ - INFO - Инициализация Crypto Analyzer
2026-04-28 20:00:00,456 - database - INFO - Таблицы успешно созданы
2026-04-28 20:00:00,789 - binance_client - INFO - Получено 100 свечей с Binance
2026-04-28 20:00:01,234 - database - INFO - Сохранена свеча за 2026-04-28 20:00:00
2026-04-28 20:00:02,345 - oscillators - INFO - Расчет осцилляторов завершен
2026-04-28 20:00:02,567 - telegram_sender - INFO - Сообщение успешно отправлено в Telegram
Мониторинг логов
bash
# Просмотр логов в реальном времени
tail -f crypto_analyzer.log

# Фильтрация ошибок
grep ERROR crypto_analyzer.log

# Последние 50 строк
tail -n 50 crypto_analyzer.log
🔒 Безопасность
Рекомендации
Никогда не коммитьте .env файл:

bash
echo ".env" >> .gitignore
Используйте сильные пароли для БД

Ограничьте доступ к серверу:

bash
# PostgreSQL: разрешить только localhost
# postgresql.conf
listen_addresses = 'localhost'
Регулярно обновляйте зависимости:

bash
pip list --outdated
pip install --upgrade <package>
Используйте виртуальное окружение:

bash
python -m venv venv
source venv/bin/activate  # Linux/macOS
venv\Scripts\activate     # Windows
Проверка безопасности
bash
# Проверка уязвимостей в зависимостях
pip install safety
safety check

# Статический анализ кода
pip install bandit
bandit -r .
🔧 Решение проблем
Часто встречающиеся ошибки
1. Ошибка подключения к PostgreSQL
text
Error: could not connect to server: Connection refused
Решение:

bash
# Проверьте статус PostgreSQL
brew services list | grep postgresql  # macOS
sudo systemctl status postgresql      # Linux

# Запустите если не работает
brew services start postgresql@15     # macOS
sudo systemctl start postgresql       # Linux
2. Ошибка аутентификации
text
Error: password authentication failed for user "postgres"
Решение:

bash
# Сброс пароля
sudo -u postgres psql
ALTER USER postgres PASSWORD 'new_password';
3. Ошибка с Docker
text
Cannot connect to the Docker daemon
Решение:

bash
# macOS
open -a Docker

# Linux
sudo systemctl start docker
4. Недостаточно данных для расчета
text
WARNING - Недостаточно данных для расчета: 14 свечей
Решение: Подождите накопления данных (нужно минимум 28 свечей)

5. Ошибка отправки в Telegram
text
ERROR - Ошибка при отправке сообщения в Telegram
Проверьте:

Правильность токена бота

Бот добавлен как администратор канала

Правильный ID канала (@username)

Диагностика
bash
# Полная диагностика системы
python main.py --test

# Проверка базы данных
psql -d crypto_analyzer -c "\dt"
psql -d crypto_analyzer -c "SELECT COUNT(*) FROM kline_data;"

# Проверка API Binance
curl "https://api.binance.com/api/v3/klines?symbol=ETHUSDT&interval=1h&limit=1"

# Проверка Telegram бота
curl "https://api.telegram.org/bot<YOUR_TOKEN>/getMe"
👨‍💻 Разработка
Добавление нового осциллятора
Добавьте метод в oscillators.py:

python
def calculate_new_oscillator(self, data):
    # Расчет
    return value, signal
Добавьте поле в модель OscillatorData в models.py:

python
new_oscillator = Column(Float, nullable=True)
new_oscillator_signal = Column(String(20), nullable=True)
Обновите скоринг в calculate_overall_score()

Добавьте в _filter_oscillator_fields() в main.py

Изменение торговой пары
В .env можно добавить:

env
SYMBOL=BTCUSDT
И обновить config.py:

python
SYMBOL = os.getenv('SYMBOL', 'ETHUSDT')
Добавление новых интервалов
В config.py:

python
INTERVAL = os.getenv('INTERVAL', '1h')  # 1h, 4h, 1d, 1w
📊 Мониторинг и статистика
График сигналов (пример)
python
# scripts/analyze_history.py
import pandas as pd
from database import db
from models import OscillatorData

with db.get_session() as session:
    data = pd.read_sql(
        session.query(OscillatorData).statement,
        session.bind
    )
    
    print("Статистика сигналов:")
    print(data['overall_signal'].value_counts())
    print(f"\nСредний скор: {data['overall_score'].mean():.2f}")
📈 Производительность
Время выполнения: ~2-5 секунд на цикл

Нагрузка на API: 1 запрос в час (лимит Binance: 1200/мин)

Размер БД: ~10-20 МБ в месяц

Память: ~50-100 МБ RAM

🤝 Вклад в проект
Форкните репозиторий

Создайте ветку (git checkout -b feature/amazing-feature)

Закоммитьте изменения (git commit -m 'Add amazing feature')

Запушьте (git push origin feature/amazing-feature)

Откройте Pull Request

📝 Changelog
v1.0.0 (2026-04-28)
✨ Первый релиз

📊 9 технических осцилляторов

💾 PostgreSQL интеграция

🤖 Telegram бот

🎯 Система скоринга

🐳 Docker поддержка

📄 Лицензия
MIT License

Copyright (c) 2026 Crypto Oscillator Analyzer

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.

## ⚠️ Дисклеймер
Данный инструмент предоставляется исключительно в информационных целях.
Торговые сигналы не являются инвестиционными рекомендациями.
Всегда проводите собственный анализ перед принятием торговых решений.

Криптовалюты являются высокорискованными активами. Торговля криптовалютами
может привести к потере всех инвестированных средств.

