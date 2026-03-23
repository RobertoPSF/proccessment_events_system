from pydantic import BaseModel
from typing import Dict, Any

class EventCreate(BaseModel):
    type: str
    payload: Dict[str, Any]
    idempotency_key: str