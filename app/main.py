from fastapi import FastAPI
from app.api.events import router as events_router

# alembic imports for programmatic migrations
from alembic import command
from alembic.config import Config
import logging

app = FastAPI()

app.include_router(events_router)


@app.on_event("startup")
def run_migrations() -> None:

    try:
        logging.info("running alembic migrations on startup")
        alembic_cfg = Config("alembic.ini")
        command.upgrade(alembic_cfg, "head")
        logging.info("migrations finished")
    except Exception as exc:
        logging.exception("failed to run migrations: %s", exc)
        raise
