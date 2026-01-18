# ML Prediction Service

ML-сервис для предсказаний с трекингом экспериментов через MLflow.

## Быстрый старт

```bash
./scripts/start.sh
# Или напрямую через docker-compose
docker-compose up -d
```

## Доступ к сервисам

| Сервис | URL | Описание |
|--------|-----|----------|
| API Docs | http://localhost:8001/docs | Swagger UI |
| MLflow UI | http://localhost:5001 | Трекинг экспериментов |
| MinIO Console | http://localhost:9001 | Хранилище артефактов (minioadmin/minioadmin) |

## API Endpoints

```bash
# Health check
curl http://localhost:8001/healthcheck

# Предсказание
curl -X POST http://localhost:8001/predict \
  -H "Content-Type: application/json" \
  -d '{"features": {"sepal_length": 5.1, "sepal_width": 3.5, "petal_length": 1.4, "petal_width": 0.2}}'

# Batch предсказание
curl -X POST http://localhost:8001/predict/batch \
  -H "Content-Type: application/json" \
  -d '{"samples": [{"sepal_length": 5.1, "sepal_width": 3.5, "petal_length": 1.4, "petal_width": 0.2}]}'

# Анализ дрифта данных
curl -X POST http://localhost:8001/data/drift \
  -H "Content-Type: application/json" \
  -d '{"current_data": [{"sepal_length": 5.1, "sepal_width": 3.5, "petal_length": 1.4, "petal_width": 0.2}]}'
```

```

## Деплой в Yandex Cloud

```bash
# Требования: yc CLI настроен (yc init)

# Полный деплой
./scripts/deploy_yc.sh full

# Только сборка и пуш образов
./scripts/deploy_yc.sh build
```

## Структура проекта

```
.
├── api/                 # FastAPI сервис
│   ├── app/
│   │   ├── main.py
│   │   ├── ml/          # ML модели и drift detection
│   │   └── routers/     # API endpoints
│   └── Dockerfile
├── mlflow/              # MLflow server
├── infrastructure/      # Terraform для YC
├── scripts/             # Скрипты запуска/деплоя
├── tests/               # Тесты и load testing
└── docker-compose.yml
```

## Переменные окружения

Скопируйте `.env.example` в `.env` перед запуском:

```bash
cp .env.example .env
```
