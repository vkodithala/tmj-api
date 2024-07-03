from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, func
from sqlalchemy.orm import relationship
from .database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    username = Column(String, nullable=False)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    entries = relationship("Entry", back_populates="created_by")


class Entry(Base):
    __tablename__ = "entries"

    id = Column(Integer, primary_key=True)
    created_by = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    date = Column(Date, server_default=func.now(), nullable=False)
