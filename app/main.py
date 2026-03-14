from fastapi import FastAPI

from app.routes import events
from app.routes import counter
from app.routes import health

app = FastAPI()

app.include_router(events.router)
app.include_router(counter.router)
app.include_router(health.router)