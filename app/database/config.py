from sqlmodel import SQLModel, create_engine, Session
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
engine = create_engine(DATABASE_URL, echo=True)

# For session handling
def get_session():
    with Session(engine) as session:
        yield session

# For table creation
def create_db_and_tables():
    from app.models.user import User
    from app.models.ticket import Ticket

    SQLModel.metadata.create_all(engine)