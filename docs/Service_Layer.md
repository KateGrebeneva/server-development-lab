# Service Layer и CRUD REST API

В проекте реализован отдельный бизнес-слой для связанных сущностей **учебный предмет (`Subject`)** и **учебная задача (`Task`)**.

## Что реализовано

- `SubjectService` — полный CRUD учебных предметов.
- `TaskService` — создание, чтение, получение списка и изменение задач через `PATCH`.
- Контроллеры не выполняют SQL-запросы и не содержат бизнес-правил: они преобразуют DTO, вызывают сервисы и формируют HTTP-ответы.
- Сервисы получают репозитории через конструктор. `TaskService` также получает функцию текущего времени (`now`), которую можно заменить фиксированным временем в тестах.
- `DomainError` и его подклассы централизованно преобразуются в HTTP-коды в `internal/controller/errors.py`.
- DTO запросов и ответов расположены в `internal/controller/dto.py`.
- При создании предмета или задачи возвращается `201 Created` и заголовок `Location`.
- При удалении возвращается `204 No Content`.

## Бизнес-правила задач

| Правило | Ошибка предметной области | HTTP |
|---|---|---:|
| Название задачи не может быть пустым | `ErrInvalidInput` | 400 |
| Приоритет может быть только `low`, `medium` или `high` | `ErrInvalidInput` | 400 |
| Срок выполнения, если указан, должен быть будущим и содержать часовой пояс | `ErrInvalidInput` | 400 |
| Предмет, к которому привязывается задача, должен существовать | `ErrNotFound` | 404 |
| Выполненную задачу нельзя повторно перевести в состояние «выполнена» или вернуть в незавершённое состояние | `ErrConflict` | 409 |

## Основные эндпоинты ЛР 7

| Метод | Путь | Назначение | Успешный код |
|---|---|---|---:|
| POST | `/api/v1/subjects` | Создать предмет | 201 + `Location` |
| GET | `/api/v1/subjects/{subject_id}` | Получить предмет | 200 |
| GET | `/api/v1/subjects?limit=20&offset=0` | Список предметов | 200 |
| PUT | `/api/v1/subjects/{subject_id}` | Полностью изменить предмет | 200 |
| DELETE | `/api/v1/subjects/{subject_id}` | Удалить предмет | 204 |
| POST | `/api/v1/tasks` | Создать задачу | 201 + `Location` |
| GET | `/api/v1/tasks/{task_id}` | Получить задачу | 200 |
| GET | `/api/v1/tasks?limit=20&offset=0` | Список задач | 200 |
| PATCH | `/api/v1/tasks/{task_id}` | Изменить поля задачи / отметить выполненной | 200 |

Для завершения задачи передайте `{"is_completed": true}` в `PATCH /api/v1/tasks/{task_id}`. Повторный запрос на завершение вернёт `409 Conflict`.

## Запуск приложения

Требуются Docker и Docker Compose.

```bash
# Выполнить один раз: создать локальный файл настроек
cp .env.example .env

# При необходимости изменить DB_PASSWORD в .env

# Запустить PostgreSQL, миграции и API
docker compose up --build -d

# Проверить доступность приложения
curl -i http://localhost:8080/api/v1/health

# Посмотреть логи
docker compose logs -f app
```

## Запуск тестов

Модульные тесты сервисного слоя не требуют БД и веб-сервера:

```bash
python -m pip install -r requirements-dev.txt
python -m pytest tests/unit -v
```

Все тесты проекта (интеграционные тесты выполняются при заданном `TEST_DATABASE_URL`):

```bash
python -m pytest -v
```

Пример запуска интеграционных тестов с отдельной тестовой БД:

```bash
# Пример для локального PostgreSQL; используйте отдельную тестовую базу
TEST_DATABASE_URL="postgresql://studly_user:password@localhost:5432/studly_test" python -m pytest tests/integration -v
```

## Приёмочная проверка

```bash
API=http://localhost:8080/api/v1

# Создать пользователя (для subject.user_id)
curl -i -X POST "$API/users" \
  -H "Content-Type: application/json" \
  -d '{"email":"student@example.com","password":"secret123","name":"Student"}'

# Создать предмет. Подставьте id пользователя вместо 1.
curl -i -X POST "$API/subjects" \
  -H "Content-Type: application/json" \
  -d '{"user_id":1,"name":"Математика","color":"#7012CE","category":"exact","time_studied_minutes":0}'

# Создать задачу. Подставьте существующий subject_id вместо 1.
curl -i -X POST "$API/tasks" \
  -H "Content-Type: application/json" \
  -d '{"subject_id":1,"title":"Решить упражнения","priority":"high","due_date":"2030-01-15T12:00:00Z"}'

# Получить список предметов с пагинацией
curl -i "$API/subjects?limit=2&offset=0"

# Отметить задачу выполненной (подставьте task_id)
curl -i -X PATCH "$API/tasks/1" \
  -H "Content-Type: application/json" \
  -d '{"is_completed":true}'

# Повторное завершение той же задачи должно вернуть 409
curl -i -X PATCH "$API/tasks/1" \
  -H "Content-Type: application/json" \
  -d '{"is_completed":true}'
```

### Ожидаемые результаты

- Создание — `201 Created` и заголовок `Location`.
- Успешное чтение и изменение — `200 OK`.
- Удаление — `204 No Content` без тела ответа.
- Неверные данные — `400 Bad Request`.
- Отсутствующая запись — `404 Not Found`.
- Повторное изменение состояния выполненной задачи — `409 Conflict`.