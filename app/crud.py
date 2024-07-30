from sqlalchemy import text
from sqlalchemy.orm import Session
from . import models, schemas


def get_user(db: Session, user_id: int):
    return db.query(models.User).filter(models.User.id == user_id).first()


def get_user_by_phone_number(db: Session, phone_number: str):
    return db.query(models.User).filter(models.User.phone_number == phone_number).first()


def get_all_users(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.User).offset(skip).limit(limit).all()


def create_user(db: Session, user: schemas.UserCreate):
    hashed_password_fake = user.password + "notReallyHashed"
    db_user = models.User(phone_number=user.phone_number,
                          hashed_password=hashed_password_fake)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user


def get_all_entries(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.Entry).offset(skip).limit(limit).all()


def create_user_entry(db: Session, entry: schemas.EntryCreate, user_id: int):
    db_entry = models.Entry(**entry.model_dump(), author_id=user_id)
    db.add(db_entry)
    db.commit()
    db.refresh(db_entry)
    return db_entry


def query_embeddings(db: Session, user_id: int, embedding: list[float]):
    sql = f"SELECT * FROM entries WHERE author_id = {user_id} ORDER BY embedding <-> '{
        embedding}' LIMIT 5;"
    return db.execute(text(sql)).fetchall()
