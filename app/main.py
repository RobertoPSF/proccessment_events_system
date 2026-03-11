import time
from fastapi import FastAPI
from .database import Base, engine

from . import models
from .routes import events

app = FastAPI()

# @app.on_event("startup")
# def startup():
#     from .models import Notification, Event

#     Base.metadata.create_all(bind=engine)


app.include_router(events.router)