# 🗃️ Слой доступа к данным Studly (паттерн Repository)

## Описание

Для лабораторной работы № 6 реализован слой доступа к данным на основе паттерна Repository. Сервисы зависят от интерфейсов репозиториев, а SQL-запросы к PostgreSQL собраны в реализациях на `asyncpg`.

Репозитории реализованы для четырёх сущностей из миграции ЛР № 5: `users`, `subjects`, `tasks`, `study_sessions`.

## Структура

```text
internal/
├── domain/
│   ├── errors.py               # доменные ошибки
│   └── models.py               # доменные модели User, Subject, Task, StudySession
├── repository/
│   ├── repository.py           # интерфейсы репозиториев (typing.Protocol)
│   └── postgres/
│       ├── db.py               # DBTX, преобразование ошибок, транзакции, пагинация
│       ├── user_repo.py
│       ├── subject_repo.py
│       ├── task_repo.py
│       └── study_session_repo.py
├── service/
│   └── study_session_service.py  # транзакционное планирование учебной сессии
└── controller/
    ├── crud_controller.py      # HTTP-эндпоинты для Swagger
    └── errors.py               # доменная ошибка -> HTTP-статус
tests/
└── integration/                # интеграционные тесты на реальной PostgreSQL
```

## Методы репозиториев

| Репозиторий | Методы |
|---|---|
| `PostgresUserRepository` | `create`, `get_by_id`, `get_by_email`, `list`, `delete`, `lock` |
| `PostgresSubjectRepository` | `create`, `get_by_id`, `list`, `update`, `delete` |
| `PostgresTaskRepository` | `create`, `get_by_id`, `list`, `update`, `delete` |
| `PostgresStudySessionRepository` | `create`, `get_by_id`, `list`, `delete`, `has_overlap` |

Правила реализации:

- только параметризованные запросы (`$1`, `$2`, ...), без склейки строк и f-строк;
- явный список столбцов вместо `SELECT *`;
- `create` использует `INSERT ... RETURNING id, created_at, updated_at`;
- `list` сортирует по `created_at DESC, id DESC`, `limit` ограничен значением 100 (по умолчанию 20);
- `update` и `delete` проверяют число затронутых строк, при 0 возвращается `ErrNotFound`;
- `password_hash` исключён из JSON (`Field(exclude=True)`).

## Ошибки

| Ситуация | Признак в PostgreSQL / asyncpg | Доменная ошибка | HTTP-статус |
|---|---|---|---|
| Запись не найдена | `fetchrow()` вернул `None`; `UPDATE 0` / `DELETE 0` | `ErrNotFound` | 404 Not Found |
| Нарушение уникальности | SQLSTATE 23505, `UniqueViolationError` | `ErrAlreadyExists` | 409 Conflict |
| Нарушение внешнего ключа | SQLSTATE 23503, `ForeignKeyViolationError` | `ErrConflict` | 409 Conflict |
| Пересечение учебных сессий | проверка в транзакции | `ErrConflict` | 409 Conflict |
| Нарушение CHECK / NOT NULL, неверный формат | SQLSTATE 23514, 23502, 22P02, `DataError` | `ErrInvalidInput` | 400 Bad Request |
| Прочие ошибки (сеть, таймаут) | любые другие | `RepositoryError` (исходная в `__cause__`) | 500 Internal Server Error |

Преобразование доменной ошибки в HTTP-статус выполняет `internal/controller/errors.py`, репозиторий ничего не знает о HTTP.

## Проверка через Swagger

Для наглядности репозитории подключены к HTTP-эндпоинтам (`internal/controller/crud_controller.py`). После `docker compose up --build -d` откройте http://localhost:8080/docs — там появятся разделы `users`, `subjects`, `tasks`, `study-sessions`. Для каждого эндпоинта в Swagger описаны возможные ошибки.

Ответ с ошибкой имеет вид `{"error": "ErrAlreadyExists", "detail": "users_email_key"}`.

| Что сделать в Swagger | Ожидаемый ответ |
|---|---|
| `POST /users` два раза с одним email | 201, затем 409 `ErrAlreadyExists` |
| `POST /users` с `"role": "hacker"` | 400 `ErrInvalidInput` (`users_role_check`) |
| `GET /users/999999` | 404 `ErrNotFound` |
| `GET /users/by-email` с email `' OR '1'='1` | 404 `ErrNotFound` — SQL-инъекция не срабатывает |
| `POST /subjects` с `"user_id": 999999` | 409 `ErrConflict` (`subjects_user_id_fkey`) |
| `POST /subjects` с `"color": "red"` | 400 `ErrInvalidInput` (`subjects_color_check`) |
| `PUT /subjects/999999` | 404 `ErrNotFound` |
| `POST /study-sessions` дважды на пересекающееся время | 201, затем 409 `ErrConflict` |
| `DELETE /users/{id}` два раза | 204, затем 404 `ErrNotFound` |
| `GET /users?limit=1` | не больше одной записи, `password_hash` в ответе нет |

Подробности ошибки PostgreSQL (`DETAIL` с содержимым строки, в том числе хешем пароля) клиенту не отдаются — только имя нарушенного ограничения.

## Транзакции (дополнительное задание)

`StudySessionService.schedule()` планирует учебную сессию в одной транзакции:

1. `SELECT ... FROM users WHERE id = $1 FOR UPDATE` — блокирует строку пользователя;
2. проверяет, нет ли у пользователя активной сессии, пересекающейся по времени;
3. вставляет новую сессию или возвращает `ErrConflict`.

Репозитории получают объект `DBTX` — его реализуют и пул `asyncpg.Pool`, и соединение транзакции `asyncpg.Connection`, поэтому одни и те же репозитории работают и вне, и внутри транзакции.

## Интеграционные тесты

Тесты выполняются на отдельной тестовой базе `studly_test`, чтобы не засорять рабочую.

Создание тестовой БД и применение миграции (PowerShell, из корня проекта, `docker compose up -d` уже выполнен):

```powershell
docker compose exec db psql -U studly_user -d studly_lab -c "CREATE DATABASE studly_test;"
docker compose run --rm migrate -path=/migrations -database "postgres://studly_user:change_me_123@db:5432/studly_test?sslmode=disable" up
```

Установка зависимостей для тестов и запуск:

```powershell
pip install -r requirements-dev.txt
$env:TEST_DATABASE_URL = "postgresql://studly_user:change_me_123@localhost:5432/studly_test"
python -m pytest -v
```

Тесты запускаются с хост-машины, поэтому в строке подключения указаны `localhost` и опубликованный порт `DB_HOST_PORT`. Если `TEST_DATABASE_URL` не задан, тесты пропускаются.

Проверяемые сценарии (24 теста):

- создание и чтение записи, `id` и `created_at` заполняются СУБД;
- чтение несуществующей записи → `ErrNotFound`;
- повторное создание пользователя с тем же email → `ErrAlreadyExists`;
- постраничная выборка возвращает не больше `limit` записей, сортировка от новых к старым;
- удаление и последующее чтение → `ErrNotFound`;
- попытка SQL-инъекции `' OR '1'='1` в `get_by_email` → `ErrNotFound`;
- обновление предмета и задачи, обновление несуществующей записи → `ErrNotFound`;
- нарушение внешнего ключа → `ErrConflict`, нарушение CHECK → `ErrInvalidInput`;
- `password_hash` не попадает в JSON;
- пересекающаяся учебная сессия отклоняется, в том числе при 5 одновременных запросах создаётся ровно одна.

---

<p align="center"><b>Studly · Server Development</b></p>
