from sqlmodel import SQLModel, Field
from typing import Optional
from enum import Enum
from sqlalchemy import Column, String

class UserRole(str, Enum):
    employee = "employee"
    agent = "agent"
    triage_officer = "triage_officer"

class UserBase(SQLModel):
    username: str = Field(sa_column=Column(String(255), unique=True, nullable=False))
    email: str    = Field(sa_column=Column(String(255), unique=True, nullable=False))
    role: UserRole = Field(sa_column=Column(String(50), nullable=False))
    department: Optional[str] = Field(default=None, sa_column=Column(String(255), nullable=True))  # New field

class User(UserBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)

class UserCreate(UserBase):
    pass

class UserRead(UserBase):
    id: int