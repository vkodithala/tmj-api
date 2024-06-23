from typing import Optional
from fastapi import Body, FastAPI
from pydantic import BaseModel

app = FastAPI()


class Post(BaseModel):
    title: str
    content: str
    published: bool = True  # setting default value for 'published'
    rating: Optional[int] = None


@app.get("/")
async def root():
    return {"message": "Hello World"}


@app.get("/getPosts")
def get_posts():
    return {"sample": "Here are your entries"}


@app.post("/sendPost")
def send_post(post: Post):
    print(post.model_dump())
    print(post.rating)
    return {f"new entry: {post.content}"}
