from typing import Sequence, Type

from sqlalchemy import ForeignKey, Boolean, String, select, ScalarResult
from sqlalchemy.ext.asyncio import AsyncSession, AsyncEngine
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column
from sqlalchemy.orm import relationship

from db.db import Base


class User(Base):
    """Creation of a user model with a set of fields and a relationship to the task model"""
    __tablename__ = "user_account"
    id: Mapped[int] = mapped_column(primary_key=True)
    telegram_id: Mapped[str] = mapped_column(index=True, unique=True)
    name: Mapped[str] = mapped_column(String)
    login: Mapped[str] = mapped_column(index=True, unique=True)
    tasks: Mapped[list["Task"]] = relationship(
        back_populates="user", cascade="all, delete-orphan", lazy='selectin'
    )

    @classmethod
    async def create_user(cls, db: AsyncSession, **kwargs) -> 'User':
        """creating a new user based on the User model"""
        transaction = cls(**kwargs)
        db.add(transaction)
        await db.commit()
        await db.refresh(transaction)
        return transaction

    @classmethod
    async def get_user_for_telegram_id(cls, db: AsyncSession, **kwargs) -> Type['User'] | None:
        """retrieving user object by telegram id"""
        telegram_id = kwargs.get("telegram_id")
        query = select(cls).where(telegram_id == cls.telegram_id)
        result = await db.scalar(query)
        return result

    @classmethod
    async def get_logins_for_cheking(cls, db: AsyncSession, **kwargs) -> ScalarResult:
        """obtaining logins to check the uniqueness of the generated login"""
        query = select(cls).where(cls.login.like(f'{kwargs.get("login")}%'))
        result = await db.scalars(query)
        return result


class Task(Base):
    __tablename__ = "task"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(70))
    description: Mapped[str]
    completed: Mapped[bool] = mapped_column(Boolean, default=False)
    user_id: Mapped[int] = mapped_column(ForeignKey("user_account.id"))
    user: Mapped["User"] = relationship(back_populates="tasks", lazy='joined', innerjoin=True)

    @classmethod
    async def create_task(cls, db: AsyncSession, **kwargs) -> 'Task':
        """creating a new task based on the Task model"""
        transaction = cls(**kwargs)
        db.add(transaction)
        await db.commit()
        await db.refresh(transaction)
        return transaction

    @classmethod
    async def get_all_my_tasks(cls, db: AsyncSession, **kwargs) -> Sequence:
        """obtaining a list of all tasks of a particular user"""
        user_id = kwargs.get("user_id")
        query = select(cls).where(cls.user_id == user_id)
        res = await db.scalars(query)
        results = res.all()
        return results

    @classmethod
    async def get_one(cls, db: AsyncSession, **kwargs) -> Type['Task'] | None:
        """obtaining a specific task by its id"""
        id = kwargs.get('id')
        result = await db.get(cls, id)
        return result

    @classmethod
    async def update_complete(cls, db: AsyncSession, **kwargs):
        """change of task status (completed/uncompleted)"""
        id = kwargs.get("id")
        task = await cls.get_one(db, id=id)
        task.completed = kwargs.get("completed")
        await db.commit()

    @classmethod
    async def delete_task(cls, db: AsyncSession, **kwargs):
        """task deletion"""
        task = await cls.get_one(db, id=kwargs.get("id"))
        await db.delete(task)
        await db.commit()
