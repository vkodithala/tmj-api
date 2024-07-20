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
    return config.Settings()


@lru_cache
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@app.get("/info/")
async def info(settings: Annotated[config.Settings, Depends(get_settings)]):
    return {
        "sendblue_apiurl": settings.sendblue_apiurl,
        "sendblue_apikey": settings.sendblue_apikey,
        "sendblue_apisecret": settings.sendblue_apisecret,
    }


@app.post("/entries/")
def create_entry(payload: helpers.MessagePayload, db: Session = Depends(get_db)):
    logger.info("Received a webhook request from SendBlue.")


@app.post("/users/", response_model=schemas.User)
def create_user(user: schemas.UserCreate, db: Session = Depends(get_db)):
    db_user = crud.get_user_by_phone_number(db, user.phone_number)
    if db_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    return crud.create_user(db=db, user=user)
