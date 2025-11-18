# Docker Setup для Table Booking Project

Этот проект использует Docker Compose для запуска Redis, Celery Worker, Celery Beat и Flower, в то время как Django и PostgreSQL работают локально на вашей машине.

## Предварительные требования

1. **Docker Desktop** установлен и запущен (Windows/Mac) или **Docker + Docker Compose** (Linux)
2. **PostgreSQL** установлен и запущен локально
3. **Python 3.11+** и виртуальное окружение
4. Файл `.env` настроен (смотрите `.env.example`)

## Структура сервисов

### Локально (на вашей машине):
- **Django** - веб-приложение (порт 8000)
- **PostgreSQL** - база данных (порт 5432)

### В Docker:
- **Redis** - брокер сообщений для Celery (порт 6379)
- **Celery Worker** - обработка асинхронных задач
- **Celery Beat** - планировщик периодических задач
- **Flower** - веб-интерфейс мониторинга Celery (порт 5555)

## Быстрый старт

### 1. Настройка окружения

Скопируйте `.env.example` в `.env` и настройте переменные:

```bash
cp .env.example .env
```

Отредактируйте `.env`:
```env
SECRET_KEY=your-secret-key
PG_NAME=table_booking
PG_USER=postgres
PG_PASSWORD=your_password
PG_HOST=127.0.0.1
REDIS_URL=redis://127.0.0.1:6379/0
```

### 2. Установка зависимостей Python

```bash
# Создайте и активируйте виртуальное окружение
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
# или
.venv\Scripts\activate  # Windows

# Установите зависимости
pip install -r requirements.txt
```

### 3. Настройка базы данных

```bash
# Создайте базу данных в PostgreSQL
createdb table_booking

# Примените миграции
python manage.py migrate

# Создайте суперпользователя
python manage.py createsuperuser
```

### 4. Запуск Docker сервисов

Запустите Redis, Celery Worker, Celery Beat и Flower:

```bash
docker-compose up -d
```

Проверьте статус контейнеров:

```bash
docker-compose ps
```

Должны быть запущены 4 контейнера:
- `table_booking_redis`
- `table_booking_celery_worker`
- `table_booking_celery_beat`
- `table_booking_flower`

### 5. Запуск Django

В отдельном терминале запустите Django сервер:

```bash
python manage.py runserver
```

## Доступ к сервисам

- **Django API**: http://localhost:8000/api/
- **Django Admin**: http://localhost:8000/admin/
- **API Документация**: http://localhost:8000/api/schema/swagger-ui/
- **Flower (Celery мониторинг)**: http://localhost:5555/

## Полезные команды

### Docker Compose

```bash
# Запустить все сервисы
docker-compose up -d

# Остановить все сервисы
docker-compose down

# Посмотреть логи всех сервисов
docker-compose logs -f

# Посмотреть логи конкретного сервиса
docker-compose logs -f celery_worker
docker-compose logs -f celery_beat
docker-compose logs -f flower

# Перезапустить конкретный сервис
docker-compose restart celery_worker

# Пересобрать образы (после изменения requirements.txt)
docker-compose build

# Остановить и удалить контейнеры + volumes
docker-compose down -v
```

### Celery

Если нужно запустить Celery команды вручную:

```bash
# Войти в контейнер celery_worker
docker-compose exec celery_worker bash

# Проверить активные задачи
docker-compose exec celery_worker celery -A reservation_System inspect active

# Очистить все задачи
docker-compose exec celery_worker celery -A reservation_System purge
```

### Django

```bash
# Применить миграции
python manage.py migrate

# Создать миграции
python manage.py makemigrations

# Создать суперпользователя
python manage.py createsuperuser

# Собрать статику
python manage.py collectstatic
```

## Проверка работоспособности

### 1. Проверка Redis

```bash
docker-compose exec redis redis-cli ping
# Должно вернуть: PONG
```

### 2. Проверка Celery Worker

Откройте Django shell и отправьте тестовую задачу:

```bash
python manage.py shell
```

```python
from reservation.tasks import send_reservation_email
result = send_reservation_email.delay('test@example.com', 'Test', 'Test message')
print(result.id)
```

Проверьте в логах Celery Worker:

```bash
docker-compose logs celery_worker
```

### 3. Проверка Celery Beat

Проверьте, что периодическая задача зарегистрирована:

```bash
docker-compose logs celery_beat | grep cleanup
```

### 4. Проверка Flower

Откройте в браузере: http://localhost:5555/

Вы должны увидеть:
- Количество активных worker'ов
- Список задач
- Графики производительности

## Устранение неполадок

### Celery не может подключиться к PostgreSQL

Убедитесь, что PostgreSQL слушает на всех интерфейсах:

**Windows/Mac (Docker Desktop):**
- `host.docker.internal` должен работать автоматически

**Linux:**
- В `postgresql.conf`: `listen_addresses = '*'`
- В `pg_hba.conf` добавьте: `host all all 172.17.0.0/16 md5`
- Перезапустите PostgreSQL

### Celery не может подключиться к Redis

```bash
# Проверьте, что Redis контейнер запущен
docker-compose ps redis

# Проверьте логи Redis
docker-compose logs redis

# Проверьте подключение
docker-compose exec redis redis-cli ping
```

### Изменения в коде не применяются

Celery использует volumes для монтирования кода. Если изменения не применяются:

```bash
# Перезапустите Celery worker и beat
docker-compose restart celery_worker celery_beat
```

### Ошибки при сборке образа

Если изменили `requirements.txt`:

```bash
# Пересоберите образы
docker-compose build --no-cache

# Перезапустите сервисы
docker-compose up -d
```

## Production

Для production окружения:

1. Используйте отдельный `.env.production` файл
2. Установите `DEBUG=False`
3. Настройте `ALLOWED_HOSTS`
4. Используйте secrets для чувствительных данных
5. Настройте Nginx как reverse proxy
6. Используйте gunicorn вместо runserver
7. Настройте мониторинг и алерты
8. Используйте Django Celery Beat для управления периодическими задачами через админку

## Дополнительно

### Очистка Docker ресурсов

```bash
# Остановить все контейнеры проекта
docker-compose down

# Удалить volumes (ВНИМАНИЕ: удалит данные Redis!)
docker-compose down -v

# Удалить неиспользуемые Docker образы
docker image prune -a
```

### Бэкап Redis данных

```bash
# Создать бэкап
docker-compose exec redis redis-cli SAVE

# Скопировать dump.rdb на хост
docker cp table_booking_redis:/data/dump.rdb ./backup/
```

## Поддержка

Если возникли проблемы:
1. Проверьте логи: `docker-compose logs -f`
2. Проверьте статус: `docker-compose ps`
3. Проверьте .env файл
4. Убедитесь, что PostgreSQL запущен локально
