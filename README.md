<h1 align="center">
  <a href="https://git.io/typing-svg">
    <img src="https://readme-typing-svg.herokuapp.com?font=DM+Serif+Display&size=30&letterSpacing=1px&pause=1000&color=A11D1E&center=true&vCenter=true&width=600&lines=Studly+%C2%B7+Server+Development" alt="Typing SVG" />
  </a>
</h1>

<p align="center">
  <b>Лабораторные работы по дисциплине «Серверная разработка»</b>
</p>

<p align="center">
  Веб-приложение <b>Studly</b> — организация и контроль учебного процесса
</p>

<br>

## 📚 Лабораторные работы

<p>
  <img src="https://i.giphy.com/media/v1.Y2lkPTc5MGI3NjExdzJiNGprcGNycDBrd2Z4dnF1aGRscnNmZnlodnY5ODliNTd5dXRhbyZlcD12MV9pbnRlcm5hbF9naWZfYnlfaWQmY3Q9cw/iEbPnIPyh9Exq/giphy.gif" width="47px"/>
  <a href="docs/ARCHITECTURE.md">Лабораторная работа №1 — Архитектура</a>
</p>

<p>
  <img src="https://i.giphy.com/media/v1.Y2lkPTc5MGI3NjExdzJiNGprcGNycDBrd2Z4dnF1aGRscnNmZnlodnY5ODliNTd5dXRhbyZlcD12MV9pbnRlcm5hbF9naWZfYnlfaWQmY3Q9cw/iEbPnIPyh9Exq/giphy.gif" width="47px"/>
  <a href="openapi.yaml">Лабораторная работа №2 — REST API / OpenAPI 3.0</a>
</p>

<p>
  <img src="https://i.giphy.com/media/v1.Y2lkPTc5MGI3NjExdzJiNGprcGNycDBrd2Z4dnF1aGRscnNmZnlodnY5ODliNTd5dXRhbyZlcD12MV9pbnRlcm5hbF9naWZfYnlfaWQmY3Q9cw/iEbPnIPyh9Exq/giphy.gif" width="47px"/>
  <a href="cmd/app/main.py">Лабораторная работа №3 — каркас приложения / Clean Architecture</a>
</p>

<p>
  <img src="https://i.giphy.com/media/v1.Y2lkPTc5MGI3NjExdzJiNGprcGNycDBrd2Z4dnF1aGRscnNmZnlodnY5ODliNTd5dXRhbyZlcD12MV9pbnRlcm5hbF9naWZfYnlfaWQmY3Q9cw/iEbPnIPyh9Exq/giphy.gif" width="47px"/>
  <a href="Dockerfile">Лабораторная работа №4 — контейнеризация / Docker</a>
</p>

<p>
  <img src="https://i.giphy.com/media/v1.Y2lkPTc5MGI3NjExdzJiNGprcGNycDBrd2Z4dnF1aGRscnNmZnlodnY5ODliNTd5dXRhbyZlcD12MV9pbnRlcm5hbF9naWZfYnlfaWQmY3Q9cw/iEbPnIPyh9Exq/giphy.gif" width="47px"/>
  <a href="docs/DATABASE.md">Лабораторная работа №5 — PostgreSQL / SQL-миграции</a>
</p>

## 💻 О проекте

**Studly** — веб-приложение для организации учебного процесса.

Сервис позволяет планировать обучение, работать с предметами и задачами, ставить цели, проводить Pomodoro-сессии, учитывать время обучения и анализировать статистику.

Также в проекте предусмотрены AI-помощники для работы с учебным материалом и отдельные возможности для родителей — просмотр прогресса учащегося.

## 🐳 Запуск в Docker

```bash
# сборка образа
docker build -t studly-api:latest .

# запуск контейнера
docker run --name studly-container -d -p 8080:8080 -e HTTP_PORT=8080 -e APP_ENV=production studly-api:latest

# проверка
curl http://localhost:8080/api/v1/health
```




## 🗄️ Лабораторная работа №5 — база данных

В проекте используется PostgreSQL с базой `studly_lab`. Миграция создаёт таблицы пользователей, предметов, задач, учебных сессий, статистики, целей и достижений.

```powershell
Copy-Item .env.example .env
docker compose up --build -d
docker compose ps -a
docker compose logs migrate
docker compose exec db psql -U studly_user -d studly_lab -c "\dt"
docker compose exec db psql -U studly_user -d studly_lab -c "SELECT version, dirty FROM schema_migrations;"
Invoke-RestMethod http://localhost:8080/api/v1/health
```

Подробные команды проверки, отката и повторного применения миграции: [docs/DATABASE.md](docs/DATABASE.md) и [LAB5_CHECKLIST.md](LAB5_CHECKLIST.md).

**Важно:** если `.env` уже существует, убедитесь, что `DB_NAME=studly_lab`. Файл `.env` не включён в архив, чтобы не передавать личные параметры подключения; создайте его из `.env.example`.
