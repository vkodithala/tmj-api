import numpy as np
from sqlalchemy import Column, Date, DateTime, Enum, Float, ForeignKey, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import ARRAY as PG_ARRAY
from sqlalchemy.orm import relationship
from .database import Base
from enum import Enum as PyEnum
from pgvector.sqlalchemy import Vector


class EmotionsEnum(str, PyEnum):
    SADNESS = "sadness"
    HAPPINESS = "happiness"
    FEAR = "fear"
    ANGER = "anger"
    SURPRISE = "surprise"
    DISGUST = "disgust"


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    phone_number = Column(String(12), nullable=False)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    hashed_password = Column(String)

    entries = relationship("Entry", back_populates="created_by")


class Entry(Base):
    __tablename__ = "entries"

    id = Column(Integer, primary_key=True)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    date = Column(Date, server_default=func.now(), nullable=False)
    emotions = Column(PG_ARRAY(Enum(EmotionsEnum)), nullable=True)
    content = Column(Text, nullable=False)
    embedding = Column(Vector(768), nullable=True)
    author_id = Column(Integer, ForeignKey("users.id"))

    created_by = relationship("User", back_populates="entries")
