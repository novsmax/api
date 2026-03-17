from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from datetime import datetime, timedelta, timezone
from typing import Optional, Tuple
import re

from app.models.user import User
from app.models.email_verification import EmailVerification
from app.models.roles import Roles
from app.models.goal_register import GoalRegister
from app.models.user_and_goal import UserAndGoal
from app.models.user_and_role import UserAndRole
from app.models.trainers import Trainer
from app.models.club_organizer import ClubOrganizer
from app.models.clubs import Club
from app.schemas.user import UserCreate
from app.core.security import get_password_hash, verify_password, generate_verification_code
from app.services.email import email_service
from app.core.config import settings

class AuthService:
    async def register_user(self, db: AsyncSession, user_data: UserCreate) -> Tuple[User, str]:
        """Регистрация нового пользователя и отправка кода подтверждения"""
        
        existing_user = await db.execute(
            select(User).where(User.email == user_data.email)
        )
        if existing_user.scalar_one_or_none():
            raise ValueError("Пользователь с таким email уже существует")
        
        existing_nickname = await db.execute(
            select(User).where(User.nickname == user_data.nickname)
        )
        if existing_nickname.scalar_one_or_none():
            raise ValueError("Пользователь с таким nickname уже существует")
        
        for goal_id in user_data.goal_ids:
            goal = await db.execute(
                select(GoalRegister).where(GoalRegister.goal_id == goal_id)
            )
            if not goal.scalar_one_or_none():
                raise ValueError("Цели регистрации с таким ID не существует")
        
        db_user = User(
            first_name=user_data.first_name,
            last_name=user_data.last_name if hasattr(user_data, 'last_name') else None,
            middle_name=user_data.middle_name if hasattr(user_data, 'middle_name') else None,
            birth_date=user_data.birth_date,
            gender=user_data.gender,
            email=user_data.email,
            nickname=user_data.nickname,
            password=get_password_hash(user_data.password),
            is_active=False
        )
        
        db.add(db_user)
        await db.flush()  

        # добавление ролей пользователю + записей в нужные схемы
        role_ids = set()
        for goal_id in user_data.goal_ids:
            db.add(UserAndGoal(user_id=db_user.user_id, goal_id=goal_id))
            goal_result = await db.execute(
                select(GoalRegister).where(GoalRegister.goal_id == goal_id)
            )
            goal = goal_result.scalar_one()
            role_ids.add(goal.id_role)

        for role_id in role_ids:
            db.add(UserAndRole(user_id=db_user.user_id, role_id=role_id))

        for role_id in role_ids:
            role_result = await db.execute(
                select(Roles).where(Roles.role_id == role_id)
            )
            role = role_result.scalar_one()
            if role.name == "trainer":
                db.add(Trainer(user_id=db_user.user_id, role_id=role_id))
            elif role.name == "club_organizer":
                db.add(ClubOrganizer(user_id=db_user.user_id, role_id=role_id, club_id=None))
        
        await db.flush()

        
        verification_code = generate_verification_code(settings.VERIFICATION_CODE_LENGTH)
        
        expires_at = datetime.now() + timedelta(minutes=settings.VERIFICATION_CODE_EXPIRE_MINUTES)
        db_verification = EmailVerification(
            user_id=db_user.user_id,
            code=verification_code,
            expires_at=expires_at
        )
        
        db.add(db_verification)
        
        try:
            await email_service.send_verification_code(db_user.email, verification_code)
        except Exception as e:
            await db.rollback()
            raise ValueError(f"Не удалось отправить письмо с подтверждением: {str(e)}")
        
        await db.commit()
        
        return db_user, verification_code
    
    async def verify_email(self, db: AsyncSession, email: str, code: str) -> Optional[User]:
        """Подтверждение email по коду"""
        
        user = await db.execute(
            select(User).where(User.email == email)
        )
        user = user.scalar_one_or_none()
        
        if not user:
            raise ValueError("Пользователь не найден")
        
        if user.is_active:
            raise ValueError("Пользователь уже подтвержден")
        
        verification = await db.execute(
            select(EmailVerification)
            .where(
                and_(
                    EmailVerification.user_id == user.user_id,
                    EmailVerification.verified_at.is_(None),
                    EmailVerification.expires_at > datetime.now()
                )
            )
            .order_by(EmailVerification.created_at.desc())
        )
        verification = verification.scalar_one_or_none()
        
        if not verification:
            raise ValueError("Не найден активный код подтверждения или срок его действия истек")
        
        if verification.attempts >= settings.MAX_VERIFICATION_ATTEMPTS:
            raise ValueError("Слишком много неверных попыток. Запросите новый код")
        
        verification.attempts += 1
        await db.flush()
        
        if verification.code != code:
            await db.commit()
            raise ValueError("Неверный код подтверждения")
        
        verification.verified_at = datetime.now()
        user.is_active = True
        
        await db.commit()
        await db.refresh(user)
        
        return user
    
    async def can_resend_code(self, db: AsyncSession, email: str) -> Tuple[bool, Optional[int]]:
        """Проверяет, можно ли отправить код повторно, и возвращает оставшееся время ожидания"""
        
        user = await db.execute(
            select(User).where(User.email == email)
        )
        user = user.scalar_one_or_none()
        
        if not user:
            raise ValueError("Пользователь не найден")
        
        if user.is_active:
            raise ValueError("Пользователь уже подтвержден")
        
        last_verification = await db.execute(
            select(EmailVerification)
            .where(EmailVerification.user_id == user.user_id)
            .order_by(EmailVerification.created_at.desc())
        )
        last_verification = last_verification.scalars().first()
        
        if not last_verification:
            return True, None
        
        time_since_last = datetime.now(timezone.utc) - last_verification.created_at
        if time_since_last.total_seconds() < settings.RESEND_COOLDOWN_SECONDS:
            remaining = settings.RESEND_COOLDOWN_SECONDS - int(time_since_last.total_seconds())
            return False, remaining
        
        return True, None
    
    async def resend_verification_code(self, db: AsyncSession, email: str) -> Tuple[str, int]:
        """Повторная отправка кода подтверждения"""
        
        can_resend, remaining = await self.can_resend_code(db, email)
        if not can_resend:
            raise ValueError(f"Подождите {remaining} секунд перед повторной отправкой")
        
        user = await db.execute(
            select(User).where(User.email == email)
        )
        user = user.scalar_one_or_none()
        
        if not user:
            raise ValueError("Пользователь не найден")
        
        if user.is_active:
            raise ValueError("Пользователь уже подтвержден")
        
        verification_code = generate_verification_code(settings.VERIFICATION_CODE_LENGTH)
        
        expires_at = datetime.now() + timedelta(minutes=settings.VERIFICATION_CODE_EXPIRE_MINUTES)
        db_verification = EmailVerification(
            user_id=user.user_id,
            code=verification_code,
            expires_at=expires_at
        )
        
        db.add(db_verification)
        
        try:
            await email_service.send_verification_code(user.email, verification_code)
        except Exception as e:
            await db.rollback()
            raise ValueError(f"Не удалось отправить письмо с подтверждением: {str(e)}")
        
        await db.commit()
        
        expires_in = int((expires_at - datetime.now()).total_seconds())
        
        return verification_code, expires_in
    
    async def check_nickname_unique(self, db: AsyncSession, nickname: str) -> Tuple[bool, str]:
        """
        Проверяет уникальность nickname.
        """
        if len(nickname) < 3:
            return False, "Никнейм должен содержать минимум 3 символа"
        if len(nickname) > 100:
            return False, "Никнейм должен содержать максимум 100 символов"
        
        if not re.match(r'^[a-zA-Z0-9_.@-]+$', nickname):
            return False, "Никнейм может содержать только буквы, цифры и символы _ . @ -"
        
        existing_user = await db.execute(
            select(User).where(User.nickname == nickname)
        )
        if existing_user.scalar_one_or_none():
            return False, "Этот никнейм уже занят"
        
        return True, "Никнейм доступен"

auth_service = AuthService()