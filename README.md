# Smart Tracker API

## Структура репозитория
```
api/
├── .env.example                # Шаблон переменных окружения
├── .gitignore
├── alembic.ini                 # Конфиг Alembic
├── Dockerfile                  # Docker образ для продакшена
├── deploy.sh                   # Скрипт быстрого деплоя
├── pytest.ini                  # Конфигурация pytest
├── migrate.py                  # Скрипт миграций с поддержкой окружений
├── requirements.txt            # Зависимости Python
├── README.md
├── .github/
│   └── workflows/
│       └── deploy.yml          # CI/CD — автодеплой при пуше в main
├── app/
│   ├── main.py                 # Точка входа FastAPI + планировщик задач
│   ├── database.py             # Подключение к БД (SQLAlchemy async)
│   ├── core/
│   │   ├── config.py           # Настройки приложения (pydantic-settings)
│   │   └── security.py         # Хэширование паролей, JWT токены
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
│   ├── api/                    # Эндпоинты
│   │   ├── auth.py             # Регистрация, верификация, логин
│   │   ├── roles.py            # Роли пользователей
│   │   ├── goals.py            # Цели регистрации
│   │   ├── password.py         # Сброс пароля
│   │   └── user_info.py        # Информация о пользователе
│   ├── services/
│   │   ├── auth.py             # Бизнес-логика авторизации
│   │   ├── email.py            # Отправка email
│   │   └── cleanup.py          # Автоудаление неподтверждённых пользователей
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
docker logs smarttracker-api --tail 50

# постоянные логи
docker logs smarttracker-api -f
```

## Фоновые задачи

При запуске приложения автоматически стартует планировщик (APScheduler), который каждый час удаляет неподтверждённых пользователей старше 24 часов.

## Эндпоинты

### Авторизация (`/auth`)
| Метод | URL | Описание |
|-------|-----|----------|
| POST | /auth/register | Регистрация пользователя |
| POST | /auth/verify-email | Подтверждение email |
| POST | /auth/resend-code | Повторная отправка кода верификации |
| POST | /auth/login | Вход в систему |
| POST | /auth/refresh | Обновление токенов |
| POST | /auth/check-nickname | Проверка доступности никнейма |

### Сброс пароля (`/password-reset`)
| Метод | URL | Описание |
|-------|-----|----------|
| POST | /password-reset/request | Запрос кода сброса пароля |
| POST | /password-reset/verify-code | Проверка кода |
| POST | /password-reset/resend-verify-code | Повторная отправка кода |
| POST | /password-reset/confirm | Смена пароля |

### Пользователь (`/user`)
| Метод | URL | Описание |
|-------|-----|----------|
| GET | /user/ | Получение информации о пользователе |
| PATCH | /user/ | Обновление информации о пользователе |
| DELETE | /user/ | Удаление пользователя |

### Роли (`/roles`)
| Метод | URL | Описание |
|-------|-----|----------|
| GET | /roles/ | Список всех ролей |
| GET | /roles/user_roles | Роли пользователя по email |

### Цели регистрации (`/goal`)
| Метод | URL | Описание |
|-------|-----|----------|
| GET | /goal/ | Список целей регистрации |

## Тестирование
```bash
pytest tests/ -v
pytest tests/test_auth.py::TestUserRegistration::test_successful_registration -v
pytest tests/ --cov=app --cov-report=term-missing
```