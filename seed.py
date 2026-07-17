"""Шаблонное заполнение БД данными о ролях пользователей и целях регистрации.

Данные лежат в app/seeds/roles.py. Запуск идемпотентен: уже существующие
строки не изменяются, добавляются только недостающие.

    python seed.py                          # DATABASE_URL из .env
    python seed.py --env prod               # DATABASE_URL из .env.production
    python seed.py --database-url "postgresql+asyncpg://..."
    python seed.py --dry-run                # только показать текущее состояние
"""

import argparse
import asyncio
import os
import sys

from dotenv import load_dotenv
from sqlalchemy import select
from sqlalchemy.ext.asyncio import create_async_engine

from app.seeds.roles import (
    GOALS,
    ROLES,
    goal_register_table,
    roles_table,
    seed_roles_and_goals,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--env', choices=['local', 'prod'], default='local',
                        help='Окружение: local (по умолчанию) или prod')
    parser.add_argument('--database-url', help='Переопределить DATABASE_URL')
    parser.add_argument('--dry-run', action='store_true',
                        help='Ничего не писать, только показать содержимое таблиц')
    return parser.parse_args()


def resolve_database_url(args: argparse.Namespace) -> str:
    if args.database_url:
        return args.database_url

    env_file = '.env.production' if args.env == 'prod' else '.env.local'
    if os.path.exists(env_file):
        load_dotenv(env_file)
        print(f"Загружено окружение: {args.env} ({env_file})")
    else:
        load_dotenv()
        print(f"Файл {env_file} не найден, загружаем .env по умолчанию")

    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        print("DATABASE_URL не задан", file=sys.stderr)
        sys.exit(1)
    return database_url


async def print_state(engine) -> None:
    async with engine.connect() as conn:
        roles = (await conn.execute(
            select(roles_table).order_by(roles_table.c.role_id)
        )).all()
        goals = (await conn.execute(
            select(goal_register_table).order_by(goal_register_table.c.goal_id)
        )).all()

    print(f"\nroles ({len(roles)}):")
    for role_id, name in roles:
        print(f"  {role_id}  {name}")

    print(f"\ngoal_register ({len(goals)}):")
    for goal_id, description, id_role in goals:
        print(f"  {goal_id}  [role={id_role}]  {description}")


async def main() -> int:
    args = parse_args()
    database_url = resolve_database_url(args)
    engine = create_async_engine(database_url)

    try:
        if args.dry_run:
            print(f"\nDry-run: шаблон содержит {len(ROLES)} ролей и {len(GOALS)} целей, "
                  f"запись не выполняется")
            await print_state(engine)
            return 0

        async with engine.begin() as conn:
            inserted = await conn.run_sync(seed_roles_and_goals)

        print(f"\nДобавлено: ролей — {inserted['roles']}, целей — {inserted['goals']} "
              f"(уже существовало: ролей — {len(ROLES) - inserted['roles']}, "
              f"целей — {len(GOALS) - inserted['goals']})")
        await print_state(engine)
        return 0
    except Exception as e:
        print(f"Ошибка: {e}", file=sys.stderr)
        return 1
    finally:
        await engine.dispose()


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
