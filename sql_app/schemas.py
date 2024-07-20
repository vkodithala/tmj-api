import datetime
from typing import List, Optional
from pydantic import BaseModel
from enum import Enum as PyEnum


class EmotionsEnum(str, PyEnum):
    SADNESS = "sadness"
    HAPPINESS = "happiness"
    FEAR = "fear"
    ANGER = "anger"
    SURPRISE = "surprise"
    DISGUST = "disgust"


class EntryBase(BaseModel):
    emotions: Optional[List[EmotionsEnum]]
    content: str
    embeddings: Optional[List[float]]


class EntryCreate(EntryBase):
    pass


class Entry(EntryBase):
    id: int
    created_at: datetime.datetime
    date: datetime.date
    author_id: int

    class Config:
        orm_mode = True


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
