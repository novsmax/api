"""Шаблонные данные о ролях пользователей и целях регистрации.

Единый источник данных для миграции `9a3f1b7c2d84_seed_roles_and_goals`
(автоматическое заполнение на свежей БД) и для скрипта `seed.py`
(ручной запуск на уже существующей БД).

Чтобы добавить роль или цель — правим списки ROLES / GOALS ниже и запускаем
`python seed.py`. Заполнение идемпотентно: существующие строки не трогаются.

Таблицы описаны через отдельную MetaData, а не через модели из app.models,
чтобы миграция не ломалась при будущих изменениях ORM-моделей.
"""

from sqlalchemy import Column, Connection, Integer, MetaData, String, Table, text
from sqlalchemy.dialects.postgresql import insert

metadata = MetaData()

roles_table = Table(
    "roles",
    metadata,
    Column("role_id", Integer, primary_key=True),
    Column("name", String(100), nullable=False, unique=True),
)

goal_register_table = Table(
    "goal_register",
    metadata,
    Column("goal_id", Integer, primary_key=True),
    Column("description", String(255), nullable=False),
    Column("id_role", Integer, nullable=False),
)

# role_id задаются явно: на них ссылаются GOALS и код в services/auth.py
ROLES: list[dict] = [
    {"role_id": 1, "name": "athlete"},
    {"role_id": 2, "name": "trainer"},
    {"role_id": 3, "name": "club_organizer"},
]

# Цели регистрации: пользователь выбирает их при регистрации, роль выводится
# из id_role выбранных целей (см. AuthService.register_user)
GOALS: list[dict] = [
    {"goal_id": 1, "description": "Следить за своими тренировками", "id_role": 1},
    {"goal_id": 2, "description": "Улучшить физическую форму", "id_role": 1},
    {"goal_id": 3, "description": "Контролировать вес", "id_role": 1},
    {"goal_id": 4, "description": "Подготовиться к соревнованиям", "id_role": 1},
    {"goal_id": 5, "description": "Тренировать спортсменов", "id_role": 2},
    {"goal_id": 6, "description": "Составлять программы тренировок", "id_role": 2},
    {"goal_id": 7, "description": "Организовать спортивный клуб", "id_role": 3},
    {"goal_id": 8, "description": "Проводить соревнования и мероприятия", "id_role": 3},
]


def _sync_sequence(connection: Connection, table: str, pk_column: str) -> None:
    """Подвинуть sequence за явно вставленные id, иначе следующий INSERT упадёт."""
    connection.execute(
        text(
            f"""
            SELECT setval(
                pg_get_serial_sequence('{table}', '{pk_column}'),
                COALESCE(MAX({pk_column}), 1),
                MAX({pk_column}) IS NOT NULL
            )
            FROM {table}
            """
        )
    )


def seed_roles_and_goals(connection: Connection) -> dict[str, int]:
    """Залить шаблонные роли и цели. Возвращает число реально вставленных строк."""
    inserted_roles = connection.execute(
        insert(roles_table).values(ROLES).on_conflict_do_nothing()
    ).rowcount
    inserted_goals = connection.execute(
        insert(goal_register_table).values(GOALS).on_conflict_do_nothing()
    ).rowcount

    _sync_sequence(connection, "roles", "role_id")
    _sync_sequence(connection, "goal_register", "goal_id")

    return {"roles": inserted_roles, "goals": inserted_goals}


def unseed_roles_and_goals(connection: Connection) -> None:
    """Удалить шаблонные строки. Упадёт, если на них уже ссылаются пользователи."""
    connection.execute(
        goal_register_table.delete().where(
            goal_register_table.c.goal_id.in_([g["goal_id"] for g in GOALS])
        )
    )
    connection.execute(
        roles_table.delete().where(
            roles_table.c.role_id.in_([r["role_id"] for r in ROLES])
        )
    )
