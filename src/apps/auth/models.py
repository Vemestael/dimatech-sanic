from typing import Optional

from pydantic import BaseModel, Field, EmailStr
from sqlalchemy import Column, Integer, String, Boolean, LargeBinary
from sqlalchemy.orm import declarative_base

Base = declarative_base()


class User(Base):
    """
    Consists of:
    username: String(150)
    password_hash: LargeBinary
    salt: LargeBinary
    email: String
    is_active: Boolean
    is_admin: Boolean
    """
    __tablename__ = 'User'

    id = Column(Integer, primary_key=True)
    username = Column(String(150), unique=True, nullable=False)
    password_hash = Column(LargeBinary, nullable=False)
    salt = Column(LargeBinary, nullable=False)
    email = Column(String(150), default='', nullable=False)
    is_active = Column(Boolean, default=False, nullable=False)
    is_admin = Column(Boolean, default=False, nullable=False)


class UserValidator(BaseModel):
    id: Optional[int]
    username: str = Field(max_length=150)
    password: str = Field(min_length=8)
    email: Optional[EmailStr]
    is_active: Optional[bool]
    is_admin: Optional[bool]


class UserDetailValidator(BaseModel):
    id: Optional[int]
    password: Optional[str] = Field(min_length=8)
    email: Optional[EmailStr]
    is_active: Optional[bool]
    is_admin: Optional[bool]
