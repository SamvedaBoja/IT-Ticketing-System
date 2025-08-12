import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import pytest
from fastapi.testclient import TestClient
from sqlmodel import SQLModel, create_engine, Session
from app.database.config import get_session
from main import app

# Load test DB URL
os.environ["DATABASE_URL"] = "mysql+pymysql://test_user:test_password@localhost/ticketing_test"
TEST_DATABASE_URL = os.getenv("DATABASE_URL")
engine = create_engine(TEST_DATABASE_URL, echo=True)


@pytest.fixture(scope="function")
def db_session():
    """
    Reset DB before each test to avoid duplicate key errors.
    """
    SQLModel.metadata.drop_all(engine)
    SQLModel.metadata.create_all(engine)

    with Session(engine) as session:
        yield session


@pytest.fixture(scope="function")
def client(db_session):
    """
    FastAPI test client with overridden DB session.
    """
    def override_get_session():
        yield db_session

    app.dependency_overrides[get_session] = override_get_session
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()