# Smart Tracker API

## Структура репозитория
```
api/
├── .env.example                # Шаблон переменных окружения
├── .gitignore
├── alembic.ini                 # Конфиг Alembic
├── Dockerfile                  # Docker образ для продакшена
├── pytest.ini                  # Конфигурация pytest
├── migrate.py                  # Скрипт миграций с поддержкой окружений
├── requirements.txt            # Зависимости Python
├── README.md
├── app/
│   ├── main.py                 # Точка входа FastAPI
│   ├── database.py             # Подключение к БД (SQLAlchemy async)
│   ├── core/
│   │   ├── config.py           # Настройки приложения (pydantic-settings)
│   │   └── security.py        # Хэширование паролей, JWT токены
│   ├── models/                 # Модели SQLAlchemy
│   │   ├── user.py
│   │   ├── email_verification.py
│   │   ├── roles.py
│   │   ├── goal_register.py
│   │   ├── user_and_goal.py
│   │   ├── user_and_role.py
│   │   ├── trainers.py
│   │   ├── clubs.py
│   │   └── club_organizer.py
│   ├── schemas/                # Pydantic схемы
│   │   ├── user.py
│   │   ├── email_verification.py
│   │   └── registration.py
│   ├── api/
│   │   └── auth.py             # Эндпоинты авторизации
│   │   └── goals.py             # Эндпоинты целей регистрации
│   │   └── roles.py             # Эндпоинты для ролей пользователя
│   ├── services/
│   │   ├── auth.py             # Бизнес-логика авторизации
│   │   └── email.py            # Отправка email
│   └── migrations/             # Миграции Alembic
│       ├── env.py
│       ├── script.py.mako
│       └── versions/
└── tests/
    ├── conftest.py
    └── test_auth.py
```

## Миграции базы данных

БД PostgreSQL 16 находится на удалённом сервере. Миграции применяются через SSH туннель с помощью `migrate.py`.

### Создать новую миграцию
```bash
python migrate.py --env prod revision --autogenerate -m "описание изменений"
```

### Применить миграции
```bash
python migrate.py --env prod upgrade head
```

### Откатить последнюю миграцию
```bash
python migrate.py --env prod downgrade -1
```

### Посмотреть историю
```bash
python migrate.py --env prod history
```

### Пересборка после изменений
```bash
docker stop smarttracker-api && docker rm smarttracker-api
docker build -t smarttracker-api .
docker run -d --name smarttracker-api --env-file ~/api/.env -p 8000:8000 smarttracker-api
```

### С помощью скрипта 
```
./deploy.sh 
```

### Просмотр логов
```
# последние логи
docker logs smarttracker-api

# постоянные логи
docker logs smarttracker-api -f
```

## Эндпоинты

| Метод | URL | Описание |
|-------|-----|----------|
| POST | /auth/register | Регистрация пользователя |
| POST | /auth/verify-email | Подтверждение email |
| POST | /auth/resend-code | Повторная отправка кода |
| POST | /auth/login | Вход в систему |
| POST | /auth/refresh | Обновление токенов |
| POST | /auth/check-nickname | Проверка доступности никнейма |
| GET | /role/check-nickname | Проверка доступности никнейма |
| GET | /role/user_roles-nickname | Проверка доступности никнейма |
| GET | /auth/check-nickname | Проверка доступности никнейма |
## Тестирование
```bash
pytest tests/ -v
pytest tests/test_auth.py::TestUserRegistration::test_successful_registration -v
pytest tests/ --cov=app --cov-report=term-missing
```