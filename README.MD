# Click Logger (FastAPI + Postgres + JS)

Быстровозводимый логер.

## Сервисы
- `tracker-service` (порт 8000): публичная точка `/t/{code}` (лог + редирект)
  - `/t/{code}` — обычный редирект
  - `/t/{code}?js=1` — промежуточная HTML-страница, которая отправит немного client-side инфы (через `sendBeacon`) и потом редиректнет
- `admin-service` (порт 8001): API для создания ссылок и просмотра кликов
  - `POST /links`
  - `GET /links`
  - `GET /clicks?code=...`
- `frontend` (порт 8080): статическая страница-админка
- `postgres` (порт 5432)

## Запуск
```bash
docker compose up --build