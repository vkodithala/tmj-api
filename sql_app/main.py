from dotenv import load_dotenv
import logging

from fastapi import Depends, FastAPI, HTTPException
from sqlalchemy.orm import Session

from sql_app import crud, models, schemas, helpers
from sql_app.database import SessionLocal, engine

models.Base.metadata.create_all(bind=engine)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
app = FastAPI()
load_dotenv()

SENDBLUE_APIURL = "https://api.sendblue.co/api/send-message"
SENDBLUE_APIKEY = "2db88f8aef896f6a5081fa1717422dd0"
SENDBLUE_APISECRET = "db14194d768044a1ac6a9ac0605b0376"

# mock change


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@app.post("/messages")
def send_message(payload: helpers.MessagePayload):
    logger.info(f"Received webhook request:")
    return payload


@app.post("/users/", response_model=schemas.User)
def create_user(user: schemas.UserCreate, db: Session = Depends(get_db)):
    db_user = crud.get_user_by_phone_number(db, user.phone_number)
    if db_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    return crud.create_user(db=db, user=user)


@app.post("/entries/", response_model=schemas.Entry)
def create_entry(entry: schemas.EntryCreate, author: str, db: Session = Depends(get_db)):
    created_by: models.User = crud.get_user_by_phone_number(db, author)
    if not created_by:
        raise HTTPException(
            status_code=404, detail="No author found with the given phone number")
    return crud.create_user_entry(db, entry, created_by.id)
