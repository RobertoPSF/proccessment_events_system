from app.database.database import engine, Base
from app.database import models

def init():
    Base.metadata.create_all(bind=engine)

if __name__ == "__main__":
    init()