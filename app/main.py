from fastapi import FastAPI
from .routes import events
from .database import Base, engine

app = FastAPI()

Base.metadata.create_all(bind=engine)

app.include_router(events.router)