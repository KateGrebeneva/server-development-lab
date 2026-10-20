# 🗄️ База данных Studly

## Описание

Для лабораторной работы № 5 серверное приложение подключается к PostgreSQL. Структура БД основана на таблицах исходного MySQL-дампа `studly_db` и перенесена в PostgreSQL.

**Имя базы данных:** `studly_lab`.

Подключение приложения выполняется через `asyncpg` с ограниченным пулом соединений. Структура БД создаётся SQL-миграцией из каталога `migrations/`.

## Используемые технологии

- PostgreSQL 16 — реляционная СУБД.
- `asyncpg` — асинхронный драйвер Python.
- Docker Compose — запуск БД, мигратора и приложения.
- `golang-migrate` — применение и откат SQL-миграций.
- `.env` — параметры подключения (не добавляется в Git).

## Таблицы базы данных

| Таблица | Назначение |
|---|---|
| `users` | Пользователи Studly, роли, email и настройки |
| `subjects` | Учебные предметы пользователя |
| `tasks` | Задачи, связанные с предметами |
| `study_sessions` | Учебные сессии и настройки Pomodoro |
| `pomodoro_intervals` | Рабочие и перерывные интервалы сессии |
| `study_time_logs` | Ежедневная статистика времени обучения |
| `goals` | Ежедневные, недельные и месячные цели |
| `activity_zones` | Оценки активности по временным интервалам |
| `achievements` | Каталог достижений |
| `user_achievements` | Прогресс достижений конкретного пользователя |
| `invitations` | Приглашения родителей и учащихся |
| `parent_children` | Связи между родителями и детьми |
| `user_invite_codes` | Персональные коды приглашения пользователя |

### Основные связи

- Один пользователь может иметь несколько предметов, целей и учебных сессий.
- У каждого предмета может быть несколько задач.
- Учебная сессия может содержать несколько Pomodoro-интервалов.
- Журнал времени связывается с пользователем, предметом и, при наличии, учебной сессией.
- Достижения пользователей хранятся в связующей таблице `user_achievements`.
- Таблица `parent_children` связывает записи пользователей в ролях родителя и ребёнка.

В миграции используются первичные и внешние ключи, `NOT NULL`, `UNIQUE`, `CHECK` и индексы по полям внешних ключей и часто используемым полям.

## Файлы миграции

```text
migrations/
├── 000001_init_schema.up.sql
└── 000001_init_schema.down.sql
```

- `up.sql` создаёт 13 таблиц, ограничения, индексы и начальный каталог достижений.
- `down.sql` удаляет созданные таблицы в обратном порядке зависимостей.

После применения миграции не следует редактировать её в уже используемой базе. Для последующих изменений создаётся новая миграция.

## Настройка `.env`

Скопируйте шаблон:

```powershell
Copy-Item .env.example .env
```

Параметры подключения в `.env.example`:

```dotenv
DB_HOST=db
DB_PORT=5432
DB_USER=studly_user
DB_PASSWORD=change_me_123
DB_NAME=studly_lab
DB_MAX_CONNS=10
```

Для локальной разработки можно изменить пароль, но он должен совпадать с `DB_PASSWORD` в настройках Docker Compose. Не публикуйте настоящий `.env` и не коммитьте его в Git.

Внутри Docker Compose приложение подключается к хосту `db` — имени сервиса PostgreSQL. Значение `localhost` внутри контейнера указывало бы на сам контейнер приложения.

## Запуск

Из корневой папки проекта в PowerShell:

```powershell
Copy-Item .env.example .env
docker compose up --build -d
docker compose ps -a
docker compose logs migrate
docker compose logs app
```

В Docker Compose используются три сервиса:

- `db` — PostgreSQL с healthcheck и именованным томом `pgdata`;
- `migrate` — применение миграций после готовности БД;
- `app` — FastAPI-приложение, которое запускается после успешного завершения миграции.

Если файл `.env` уже существует, `Copy-Item` сообщит об этом. В таком случае проверьте, что в нём задано `DB_NAME=studly_lab`.

## Проверка таблиц и миграции

```powershell
docker compose exec db psql -U studly_user -d studly_lab -c "\dt"
docker compose exec db psql -U studly_user -d studly_lab -c "SELECT version, dirty FROM schema_migrations;"
```

Ожидаются 13 таблиц приложения и служебная таблица `schema_migrations`. После успешного применения единственной миграции ожидаются `version = 1` и `dirty = f`.

Проверить записи каталога достижений:

```powershell
docker compose exec db psql -U studly_user -d studly_lab -c "SELECT code, title FROM achievements ORDER BY id;"
```

## Проверка health endpoint

```powershell
Invoke-RestMethod http://localhost:8080/api/v1/health
```

При доступной БД приложение возвращает HTTP 200. Если БД недоступна, endpoint должен возвращать HTTP 503.

## Проверка сохранности данных

```powershell
docker compose down
docker compose up -d
docker compose exec db psql -U studly_user -d studly_lab -c "SELECT count(*) FROM achievements;"
```

Именованный том `pgdata` сохраняет данные после остановки контейнеров. Не используйте `docker compose down -v`, если нужно сохранить данные: флаг `-v` удаляет том базы данных.

## Откат и повторное применение миграции

Перед откатом убедитесь, что не требуется сохранять данные: `down 1` удаляет таблицы, созданные миграцией.

```powershell
docker compose run --rm migrate -path=/migrations -database "postgres://studly_user:change_me_123@db:5432/studly_lab?sslmode=disable" down 1
docker compose exec db psql -U studly_user -d studly_lab -c "\dt"
docker compose run --rm migrate -path=/migrations -database "postgres://studly_user:change_me_123@db:5432/studly_lab?sslmode=disable" up
```

Если изменили `DB_USER` или `DB_PASSWORD` в `.env`, замените эти значения в строке подключения к мигратору. После отката служебная таблица мигратора может оставаться; при повторном применении ожидается создание таблиц приложения.

## Принципы проектирования

1. **Целостность данных** — связи и ограничения защищают данные от некорректных значений.
2. **Нормализация** — пользователи, предметы, задачи, сессии и статистика разделены по сущностям.
3. **Версионирование** — структура базы управляется миграциями.
4. **Безопасная конфигурация** — параметры подключения передаются через переменные окружения.
5. **Сохранность** — данные PostgreSQL хранятся в именованном томе Docker.

## Документация

- [PostgreSQL](https://www.postgresql.org/docs/)
- [Docker Compose](https://docs.docker.com/compose/)
- [asyncpg](https://magicstack.github.io/asyncpg/current/)
- [golang-migrate](https://github.com/golang-migrate/migrate)

---

<p align="center"><b>Studly · Server Development</b></p>
