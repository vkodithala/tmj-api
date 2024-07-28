from functools import lru_cache
from typing import Annotated
from dotenv import load_dotenv
import logging

from fastapi import Depends, FastAPI, HTTPException
from sqlalchemy.orm import Session
from pgvector.sqlalchemy import Vector

from app import crud, models, schemas, helpers, config, constants, tokenizer, utils
from app.database import SessionLocal, engine

models.Base.metadata.create_all(bind=engine)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
app = FastAPI()

load_dotenv()


@lru_cache
def get_settings():
    return config.Settings()  # type: ignore


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@app.post("/entries/")
async def create_entry(payload: utils.MessagePayload, settings: Annotated[config.Settings, Depends(get_settings)], db: Session = Depends(get_db)):
    logger.info("Received a webhook request from SendBlue.")
    user_phone, content, date_sent = payload.from_number, payload.content, payload.date_sent
    user = crud.get_user_by_phone_number(db, user_phone)
    if not user:
        raise HTTPException(
            status_code=404, detail="User with phone number not found in database.")
    crud.query_embeddings(
        db, user.id, tokenizer.embed(content))  # type: ignore

    response = helpers.generate_response(
        user_phone, content, date_sent, logger, settings, db)
    entry_embedding = tokenizer.embed(content)
    entry_data = schemas.EntryCreate(
        content=content, embedding=entry_embedding, emotions=None)
    new_entry = crud.create_user_entry(db, entry_data, user.id)  # type: ignore
    to_return = await helpers.send_message(user_phone, response, settings)
    return response


@app.post("/users/", response_model=schemas.User)
async def create_user(user: schemas.UserCreate, settings: Annotated[config.Settings, Depends(get_settings)], db: Session = Depends(get_db)):
    db_user = crud.get_user_by_phone_number(db, user.phone_number)
    if db_user:
        raise HTTPException(
            status_code=400, detail="Email already registered!")
    crud.create_user(db=db, user=user)
    response = await helpers.send_message(user.phone_number, constants.welcome_message, settings)
    return response
