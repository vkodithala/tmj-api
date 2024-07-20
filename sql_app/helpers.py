from typing import Optional
from pydantic import BaseModel


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
    was_downgraded: bool
    plan: str
