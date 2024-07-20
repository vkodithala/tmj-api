from functools import lru_cache
from typing import Annotated
from dotenv import load_dotenv
import logging

from fastapi import Depends, FastAPI, HTTPException
from sqlalchemy.orm import Session

from app import crud, models, schemas, helpers, config
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
async def create_entry(payload: helpers.MessagePayload, settings: Annotated[config.Settings, Depends(get_settings)], db: Session = Depends(get_db)):
    logger.info("Received a webhook request from SendBlue.")
    user_phone, content, date_sent = payload.from_number, payload.content, payload.date_sent
    user = crud.get_user_by_phone_number(db, user_phone)
    if not user:
        raise HTTPException(
            status_code=404, detail="User with phone number not found in database.")
    entry_data = schemas.EntryCreate(
        content=content, embeddings=None, emotions=None)
    new_entry = crud.create_user_entry(db, entry_data, user.id)  # type: ignore
    logger.info(new_entry)
    response = helpers.generate_response(user_phone, content, date_sent)
    to_return = await helpers.send_message(user_phone, response, settings)
    return to_return


@app.post("/users/", response_model=schemas.User)
def create_user(user: schemas.UserCreate, db: Session = Depends(get_db)):
    db_user = crud.get_user_by_phone_number(db, user.phone_number)
    if db_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    return crud.create_user(db=db, user=user)
