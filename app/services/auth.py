from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from datetime import datetime, timedelta, timezone
from typing import Optional, Tuple

from app.models.user import User
from app.models.email_verification import EmailVerification
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
            raise ValueError("User with this email already exists")
        
        existing_nickname = await db.execute(
            select(User).where(User.nickname == user_data.nickname)
        )
        if existing_nickname.scalar_one_or_none():
            raise ValueError("User with this nickname already exists")
        
        db_user = User(
            first_name=user_data.first_name,
            birth_date=user_data.birth_date,
            gender=user_data.gender,
            email=user_data.email,
            nickname=user_data.nickname,
            password=get_password_hash(user_data.password),
            is_active=False
        )
        
        db.add(db_user)
        await db.flush()  
        
        await db.execute(
            select(EmailVerification)
            .where(
                and_(
                    EmailVerification.user_id == db_user.user_id,
                    EmailVerification.verified_at.is_(None)
                )
            )
        )
        
        verification_code = generate_verification_code(settings.VERIFICATION_CODE_LENGTH)
        
        expires_at = datetime.now() + timedelta(minutes=settings.VERIFICATION_CODE_EXPIRE_MINUTES)
        db_verification = EmailVerification(
            user_id=db_user.user_id,
            code=verification_code,
            expires_at=expires_at
        )
        
        db.add(db_verification)
        await db.commit()
        
        await email_service.send_verification_code(db_user.email, verification_code)
        
        return db_user, verification_code
    
    async def verify_email(self, db: AsyncSession, email: str, code: str) -> Optional[User]:
        """Подтверждение email по коду"""
        
        user = await db.execute(
            select(User).where(User.email == email)
        )
        user = user.scalar_one_or_none()
        
        if not user:
            raise ValueError("User not found")
        
        if user.is_active:
            raise ValueError("User already verified")
        
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
            raise ValueError("No active verification found or code expired")
        
        if verification.attempts >= settings.MAX_VERIFICATION_ATTEMPTS:
            raise ValueError("Too many failed attempts")
        
        verification.attempts += 1
        await db.flush()
        
        if verification.code != code:
            await db.commit()
            raise ValueError("Invalid verification code")
        
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
            raise ValueError("User not found")
        
        if user.is_active:
            raise ValueError("User already verified")
        
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
            raise ValueError(f"Please wait {remaining} seconds before resending")
        
        user = await db.execute(
            select(User).where(User.email == email)
        )
        user = user.scalar_one_or_none()
        
        if not user:
            raise ValueError("User not found")
        
        if user.is_active:
            raise ValueError("User already verified")
        
        verification_code = generate_verification_code(settings.VERIFICATION_CODE_LENGTH)
        
        await db.execute(
            select(EmailVerification)
            .where(
                and_(
                    EmailVerification.user_id == user.user_id,
                    EmailVerification.verified_at.is_(None)
                )
            )
        )
        
        expires_at = datetime.now() + timedelta(minutes=settings.VERIFICATION_CODE_EXPIRE_MINUTES)
        db_verification = EmailVerification(
            user_id=user.user_id,
            code=verification_code,
            expires_at=expires_at
        )
        
        db.add(db_verification)
        await db.commit()
        
        await email_service.send_verification_code(user.email, verification_code)
        
        expires_in = int((expires_at - datetime.now()).total_seconds())
        
        return verification_code, expires_in

auth_service = AuthService()