import requests
from typing import Annotated, Optional
from fastapi import Depends
from pydantic import BaseModel

from app import config


class MessagePayload(BaseModel):
    accountEmail: str
    content: str
    media_url: str
    is_outbound: bool
    status: str
    error_code: Optional[int]
    error_message: Optional[str]
    message_handle: str
    date_sent: str
    date_updated: str
    from_number: str
    number: str
    was_downgraded: Optional[bool]
    plan: str


def generate_response(user_phone: str, content: str, date_sent: str):
    return f"Received the message from {user_phone} with content {content} on date {date_sent}."


async def send_message(user_phone: str, response: str, settings: config.Settings):
    headers = {
        "sb-api-key-id": settings.sendblue_apikey,
        "sb-api-secret-key": settings.sendblue_apisecret,
        "Content-Type": "application/json"
    }
    data = {
        "number": user_phone,
        "content": response,
    }
    sendblue_response = requests.post(
        settings.sendblue_apiurl, headers=headers, json=data)
    return sendblue_response.json
