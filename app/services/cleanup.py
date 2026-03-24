from sqlalchemy import select
from datetime import datetime, timezone, timedelta
from app.models.user import User
from app.database import AsyncSessionLocal


async def delete_unverified_users():
    """Удаляет неподтверждённых пользователей старше 24 часов"""
    async with AsyncSessionLocal() as db:
        cutoff = datetime.now(timezone.utc) - timedelta(hours=24)
        
        result = await db.execute(
            select(User).where(
                User.is_active == False,
                User.created_at < cutoff
            )
        )
        users = result.scalars().all()
        
        for user in users:
            await db.delete(user)
        
        await db.commit()
        print(f"[Cleanup] Удалено неподтверждённых пользователей: {len(users)}")