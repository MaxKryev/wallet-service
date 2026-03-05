# Wallet Service

REST API для управления кошельками пользователей на базе FastAPI + PostgreSQL.

## Оглавление
- [Особенности](#особенности)
- [Требования](#требования)
- [Установка](#установка)
- [Тестирование приложения](#7-тестирование)
- [Code Quality](#8-code-quality)
- [Структура проекта](#структура-проекта)
- [API Документация](#api-документация)
- [Переменные окружения](#переменные-окружения-env)

---

## Особенности

### Безопасность и надёжность
- **Защита от race conditions**: Использование `SELECT ... FOR UPDATE` (pessimistic locking) гарантирует корректную обработку параллельных запросов на изменение баланса одного кошелька.
- **Точные финансовые расчёты**: Тип `Decimal` (Python) + `NUMERIC(15,2)` (PostgreSQL) — никаких ошибок округления `float`.
- **Валидация входных данных**: Pydantic v2 схемы обеспечивают строгую проверку:
  - Только операции `DEPOSIT` / `WITHDRAW`
  - Сумма > 0
  - Не более 2 знаков после запятой

### Производительность
- **Асинхронный стек**: FastAPI + asyncpg + SQLAlchemy 2.0 (полный `async/await`)
- **Connection pooling**: Оптимизированное управление соединениями с БД
- **Hot-reload**: Авто-перезагрузка сервера при изменении кода в режиме разработки

### Качество кода
- **Полное покрытие тестами**: pytest + httpx, включая тесты на конкурентность
- **Статическая типизация**: mypy с плагином для SQLAlchemy
- **Авто-форматирование**: black + isort
- **Линтинг**: flake8 с настройками под PEP8

### Инфраструктура
- **Docker Compose**: Вся система (app + PostgreSQL) поднимается одной командой
- **Alembic**: Управление миграциями базы данных
- **Poetry**: Современное управление зависимостями с фиксацией версий (`poetry.lock`)

---

## Требования

| Компонент | Версия | Зачем |
|-----------|--------|-------|
| Python | 3.12 | Язык приложения |
| Poetry | 1.7+ | Управление зависимостями |
| Docker | 24+ | Контейнеризация |
| Docker Compose | 2.20+ | Оркестрация контейнеров |
| PostgreSQL | 15+ | Хранение данных (в Docker) |

---

## Установка

### 1. Клонировать репозиторий
```bash
git clone https://github.com/твой-username/wallet-service.git
cd wallet-service
```

### 2. Установить зависимости через Poetry
```bash
poetry install
```

### 3. Создать файл окружения
```bash
cp .env.example .env
```

### 4. Применить миграции (локально)
```bash
poetry run alembic upgrade head
```

### 5. Локальный запуск (рекомендуется для разработки)
```bash
# 1. Запусти PostgreSQL локально
docker run -d -p 5432:5432 -e POSTGRES_PASSWORD=postgres -e POSTGRES_DB=wallet_db postgres:15-alpine

# 2. Примени миграции
poetry run alembic upgrade head

# 3. Запусти сервер с авто-перезагрузкой
poetry run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Приложение доступно по адресу: http://localhost:8000

### 6. Запуск через Docker (рекомендуется для тестирования/прода)
Запусти всю систему одной командой
```bash
docker-compose up --build -d
```
Проверь статус контейнеров
```bash
docker-compose ps
```
Открой документацию API
http://localhost:8000/docs

Просмотр логов
```bash
docker-compose logs -f app
```
Остановка
```bash
docker-compose down
```

### 7. Тестирование
Запуск тестов в Docker-контейнере
```bash
docker-compose exec app poetry run pytest tests/ -v
```
Запуск тестов локально
```bash
poetry run pytest tests/ -v
```

### 8. Code Quality
Запуск линтеров, автоформаттеров и проверки аннотации типов
```bash
poetry run black app tests && poetry run isort app tests && poetry run flake8 app tests && poetry run mypy app
```

## Структура проекта
```plaintext
wallet_service/
├── alembic/versions/                 # Файлы миграций
├── app/
│   ├── api/v1/endpoints/wallets.py   # Эндпоинты API
│   ├── api/v1/router.py              # Маршрутизатор эндпоинтов
│   ├── core/config.py                # Настройки через Pydantic
│   ├── db/session.py                 # Асинхронная сессия БД
│   ├── db/base.py                    # Базовый класс SQLAlchemy
│   ├── models/wallet.py              # SQLAlchemy модель
│   ├── schemas/wallet.py             # Pydantic схемы
│   ├── services/wallet.py            # Бизнес-логика
│   └── main.py                       # Точка входа FastAPI
├── tests/
│   ├── conftest.py                   # Фикстуры pytest
│   └── test_wallets.py               # Тесты эндпоинтов
├── .dockerignore                     # Файл dockerignore
├── .env                              # Файл секретов
├── .gitignore                        # Файл gitignore
├── alembic.ini                       # Конфигурация alembic
├── docker-compose.yml                # Оркестрация контейнеров
├── Dockerfile                        # Образ приложения
├── poetry.lock                       # Зафиксированные версии
├── pyproject.toml                    # Зависимости Poetry
└── README.md                         # Документация проекта
```

## API Документация

Swagger UI
http://localhost:8000/docs

### Основные эндпоинты
1. Получить баланс кошелька

```bash
GET /api/v1/wallets/{wallet_id}
```

2. Изменить баланс (депозит или снятие)

```bash
POST /api/v1/wallets/{wallet_id}/operation
Content-Type: application/json
```

3. Health Check

```bash
GET /health
```

## Переменные окружения (.env)

```bash
DB_USER=postgres
DB_PASS=postgres
DB_NAME=wallet_db
DB_HOST=localhost
DB_PORT=5432
APP_HOST=0.0.0.0
APP_PORT=8000
```