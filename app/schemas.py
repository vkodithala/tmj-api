import datetime
from typing import List, Optional
import numpy as np
from pydantic import BaseModel, ConfigDict
from enum import Enum as PyEnum
from pgvector.sqlalchemy import Vector


class EntryBase(BaseModel):
    emotions: Optional[List[str]]
    content: str
    embedding: Optional[List[float]]

    class Config:
        orm_mode = True
        arbitrary_types_allowed = True


class EntryCreate(EntryBase):
    pass


class Entry(EntryBase):
    id: int
    created_at: datetime.datetime
    date: datetime.date
    author_id: int


class UserBase(BaseModel):
    phone_number: str


class UserCreate(UserBase):
    password: str


class User(UserBase):
    id: int
    created_at: datetime.datetime
    entries: list[Entry] = []

    class Config:
        orm_mode = True
