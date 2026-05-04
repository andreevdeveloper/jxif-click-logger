import time
from sqlmodel import SQLModel, Session, create_engine
from sqlalchemy.exc import OperationalError

from common.settings import settings

engine = create_engine(settings.database_url, pool_pre_ping=True)

def create_db_and_tables() -> None:

    last_err = None
    for _ in range(30):
        try:
            SQLModel.metadata.create_all(engine)
            return
        except OperationalError as e:
            last_err = e
            time.sleep(1)
    raise last_err

def get_session():
    with Session(engine) as session:
        yield session