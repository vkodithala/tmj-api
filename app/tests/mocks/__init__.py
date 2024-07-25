from app.models import EmotionsEnum


mock_create_user_payload = {
    "phone_number": "+16788973910",
    "password": "MockHashedPassword"
}

mock_create_user_response = {
    "phone_number": "+16788973910",
    "id": 5,
    "created_at": "2024-07-22T23:50:13.782002",
    "entries": []
}

mock_get_user_response = {
    "id": 1,
    "phone_number": "+16788973910",
    "created_at": "2024-07-22T23:50:13.782002",
    "hashed_password": "MockHashedPassword"
}

mock_create_user_entry_response = {
    "id": 1,
    "created_at": "2024-07-24T12:00:00.000000",
    "date": "2024-07-24",
    "emotions": ["happiness", "surprise"],
    "content": "This is a mock entry content.",
    "embedding": None,
    "author_id": 1,
    "created_by": {
        "id": 1,
        "phone_number": "+16788973910",
        "created_at": "2024-07-01T10:00:00.000000"
    }
}

mock_message_payload = {
    "accountEmail": "varoon.kodithala@gmail.com",
    "content": "MockMessage",
    "is_outbound": False,
    "status": "RECEIVED",
    "error_code": None,
    "error_message": None,
    "error_reason": None,
    "message_handle": "E0F8050E-1357-4B21-9954-3C3AC3921FD2",
    "date_sent": "2024-07-23T03:37:08.648Z",
    "date_updated": "2024-07-23T03:37:09.283Z",
    "from_number": "+16788973910",
    "number": "+16788973910",
    "to_number": "+16193138272",
    "was_downgraded": None,
    "plan": "blue",
    "media_url": "",
    "message_type": "message",
    "group_id": "",
    "participants": [
        "+16788973910"
    ],
    "send_style": "",
    "opted_out": False,
    "error_detail": None
}

mock_send_message_response = {
    "status_code": 202,
}

mock_entry_create_response = {
    "id": 1,
    "created_at": "2024-07-01T10:00:00.000000",
    "date": "2024-07-01",
    "author_id": 3,
    "emotions": [EmotionsEnum.HAPPINESS, EmotionsEnum.SURPRISE],
    "content": "Today was an amazing day! I got a promotion at work and my best friend threw me a surprise party.",
    "embedding": [0.1, 0.2, 0.3, 0.4, 0.5]
}
