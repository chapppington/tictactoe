# TicTacToe API

Backend API для игры в крестики-нолики. Игроки могут создавать игры, присоединяться к ним и играть через REST API с real-time обновлениями через WebSocket.

**Фронтенд:** [tictactoe_frontend](https://github.com/chapppington/tictactoe_frontend)

## Технологии

- **Python 3.13** — асинхронный код
- **FastAPI** — веб-фреймворк
- **PostgreSQL** — база данных
- **MongoDB** — хранилище игр и ходов
- **JWT** — аутентификация через cookies
- **WebSocket** — real-time обновления игры
- **Docker** — контейнеризация

## Быстрый старт

```bash
# 1. Запуск всех сервисов
make all

# 2. Применение миграций
make migrate

# 3. Проверка работы
curl http://localhost:8000/healthcheck
```

API документация: **http://localhost:8000/api/docs**

## API эндпоинты

### Аутентификация

- `POST /api/v1/auth/register` — регистрация
  - Body: `{ email, password, name }`
  
- `POST /api/v1/auth/login` — вход
  - Body: `{ email, password }`
  - Устанавливает токены в cookies

- `POST /api/v1/auth/token/refresh` — обновление токена

### Игры

- `POST /api/v1/games` — создать игру (требует авторизацию)
  - Создатель становится игроком X
  
- `GET /api/v1/games` — список ожидающих игр
  - Query: `limit`, `offset`

- `GET /api/v1/games/my` — мои игры (требует авторизацию)
  - Query: `status`, `limit`, `offset`

- `GET /api/v1/games/{game_id}` — информация об игре

- `POST /api/v1/games/{game_id}/join` — присоединиться к игре (требует авторизацию)
  - Присоединившийся становится игроком O

- `POST /api/v1/games/{game_id}/move` — сделать ход (требует авторизацию)
  - Body: `{ row: 0-2, col: 0-2 }`

- `GET /api/v1/games/{game_id}/moves` — история ходов

### WebSocket

- `WS /api/v1/games/{game_id}/ws` — подключение к игре
  - Требует авторизацию через cookie или header
  - Отправляет обновления в реальном времени

## Статусы игры

- `waiting` — ожидает второго игрока
- `active` — игра идет
- `finished` — игра завершена

## Правила игры

- Игрок X ходит первым
- Ходы чередуются между X и O
- Победа: 3 символа в ряд (горизонталь, вертикаль, диагональ)
- Ничья: доска заполнена без победителя

## Команды

### Управление сервисами

```bash
make all          # Запуск всех сервисов
make all-down      # Остановка всех сервисов
make app-up        # Запуск только приложения
make storages      # Запуск только баз данных
```

### Миграции

```bash
make migrations    # Создать миграцию
make migrate       # Применить миграции
```

### Разработка

```bash
make test         # Запуск тестов
make precommit    # Проверка кода
make app-shell    # Войти в контейнер
```

## Структура проекта

```
app/
├── domain/          # Бизнес-логика (игры, пользователи)
├── application/    # Use cases (команды и запросы)
├── infrastructure/ # Репозитории, базы данных, WebSocket
└── presentation/   # API эндпоинты
```

## Тестирование

Проект включает тесты:
- Unit-тесты доменной логики
- Integration тесты use cases
- E2E тесты API эндпоинтов

```bash
make test
```

## Архитектура

Проект использует:
- **DDD** — разделение на слои (domain, application, infrastructure, presentation)
- **CQRS** — разделение команд и запросов
- **Dependency Injection** — через контейнер punq
- **Mediator** — централизованная обработка команд/запросов
