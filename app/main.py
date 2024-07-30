from datetime import timedelta
from functools import lru_cache, wraps
import json
from typing import Annotated
from dotenv import load_dotenv
from contextlib import asynccontextmanager
import logging
import redis

from fastapi import Depends, FastAPI, HTTPException
from sqlalchemy.orm import Session
from pgvector.sqlalchemy import Vector

from app import crud, models, schemas, helpers, config, constants, tokenizer, utils
from app.database import SessionLocal, engine

models.Base.metadata.create_all(bind=engine)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # code to run on startup
    load_dotenv()
    # Redis cache initialization
    app.state.redis_client = redis.Redis(
        host='localhost', port=6379, db=0, decode_responses=True)
    logger.info(f"Redis connection details: {
                app.state.redis_client.connection_pool.connection_kwargs}")
    yield
    # code to run on shutdown

app = FastAPI(lifespan=lifespan)


@lru_cache
def get_settings():
    return config.Settings()  # type: ignore


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_redis_client():
    return app.state.redis_client


def cache_entry(redis_client: redis.Redis, user_phone: str, content: str, response: str, date_sent: str) -> bool:
    try:
        key = f"user:{user_phone}:entries"
        entry_data = {
            "message": content,
            "response": response,
            "date_sent": date_sent
        }
        entry_json = json.dumps(entry_data)

        expire_time = int(timedelta(hours=24).total_seconds())
        # using Redis pipeline for atomic writes
        with redis_client.pipeline() as pipe:
            pipe.lpush(key, entry_json)
            pipe.ltrim(key, 0, 99)
            pipe.expire(key, expire_time)
            results = pipe.execute()
        return True
    except redis.RedisError as e:
        logger.error(f"Error storing data in Redis cache: {e}")
        return False


def get_session_history(redis_client: redis.Redis, user_phone: str):
    key = f"user:{user_phone}:entries"
    try:
        logger.info(f"KEY: {key}")
        data = redis_client.lrange(key, 0, -1)
        escaped_data = [entry.replace("{", "{{").replace("}", "}}")
                        for entry in data]  # type: ignore
        return escaped_data
    except redis.RedisError as e:
        logger.error(f"Error reading from Redis: {e}.")


@app.post("/entries/")
async def create_entry(payload: utils.MessagePayload, settings: Annotated[config.Settings, Depends(get_settings)],
                       db: Session = Depends(get_db), redis_client: redis.Redis = Depends(get_redis_client)):
    logger.info("Received a webhook request from SendBlue.")
    user_phone, content, date_sent = payload.from_number, payload.content, payload.date_sent
    user = crud.get_user_by_phone_number(db, user_phone)
    if not user:
        raise HTTPException(
            status_code=404, detail="User with phone number not found in database.")
    crud.query_embeddings(
        db, user.id, tokenizer.embed(content))  # type: ignore

    response = helpers.generate_response(
        user_phone, content, date_sent, logger, settings, db, redis_client)
<<<<<<< HEAD

    await helpers.send_message(user_phone, response, settings)

=======
>>>>>>> 1617e842aab080011314d9a89f98dc4fe27b9ae8
    entry_embedding = tokenizer.embed(content)
    # emotion = tokenizer.emotion(content)
    entry_data = schemas.EntryCreate(
<<<<<<< HEAD
        content=content, embedding=entry_embedding, emotions="")
=======
        content=content, embedding=entry_embedding, emotions=None)
>>>>>>> 1617e842aab080011314d9a89f98dc4fe27b9ae8

    cache_success = cache_entry(
        redis_client, user_phone, content, response, date_sent)
    logger.info(f"Cache operation {
                'succeeded' if cache_success else 'failed'}.")

    crud.create_user_entry(db, entry_data, user.id)  # type: ignore
<<<<<<< HEAD
=======
    await helpers.send_message(user_phone, response, settings)

>>>>>>> 1617e842aab080011314d9a89f98dc4fe27b9ae8
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
