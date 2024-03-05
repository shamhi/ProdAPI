Чтобы запустить два контейнера Docker (один для приложения FastAPI и другой для PostgreSQL) и связать их между собой без использования Docker Compose, вы можете использовать следующие шаги:

1. Создайте пользовательскую сеть Docker с помощью команды docker network create:
```bash
docker network create mynetwork
```
Эта команда создает новую сеть с именем mynetwork.

2. Создайте образ в директории, где находится Dockerfile с помощью команды:
```bash
docker build . -t fastapi_image
```

3. Запустите контейнер PostgreSQL и подключите его к сети mynetwork с помощью команды docker run:
```bash
docker run -d --name db \
  --network mynetwork \
  -e POSTGRES_USER=myuser \
  -e POSTGRES_PASSWORD=mypassword \
  -e POSTGRES_DB=mydb \
  postgres:latest
```
Эта команда запускает новый контейнер PostgreSQL с именем db, подключает его к сети mynetwork и устанавливает переменные среды POSTGRES_USER, POSTGRES_PASSWORD и POSTGRES_DB для настройки базы данных.

4. Запустите контейнер FastAPI и подключите его к сети mynetwork с помощью команды docker run:
```bash
docker run -d --name app \
  --network mynetwork \
  -p 8080:8080 \
  -e POSTGRES_CONN=postgresql+asyncpg://myuser:mypassword@db:5432/mydb \
  fastapi_image
```
Эта команда запускает новый контейнер FastAPI с именем app, подключает его к сети mynetwork, отображает порт 8000 на хосте на порт 8000 в контейнере и устанавливает переменную среды DATABASE_URL для настройки подключения к базе данных.

5. Проверьте, что оба контейнера работают и могут общаться друг с другом, используя команду docker ps:
docker ps
Эта команда должна показать список запущенных контейнеров, включая контейнеры app и db.

6. Вы можете проверить, что приложение FastAPI может подключиться к базе данных PostgreSQL, используя URL-адрес http://db:5432 внутри контейнера FastAPI. Например, вы можете использовать команду curl внутри контейнера FastAPI, чтобы проверить подключение к базе данных:
```bash
docker exec -it app sh -c "curl -s http://db:5432"
```
Эта команда должна вернуть сообщение об ошибке, потому что по умолчанию PostgreSQL не разрешает подключения по протоколу HTTP. Однако, если вы настроили базу данных для разрешения подключений по протоколу HTTP, вы должны увидеть страницу входа PostgreSQL.

Команды docker network create, docker run и docker ps полезны для управления контейнерами Docker и сетями. Вы можете использовать эти команды для создания сложных архитектур приложений, состоящих из нескольких контейнеров, связанных между собой.