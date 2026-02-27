import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import app.models.capture_item  # noqa: F401
import app.models.checklist_item  # noqa: F401
import app.models.completion_log  # noqa: F401
import app.models.task  # noqa: F401
from app.db.base import Base
from app.db.session import get_db
from main import app

TEST_DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

TASK_PAYLOAD = {
    "title": "テストタスク",
    "task_type": "execution",
    "priority": "must",
    "done_criteria": "完了基準",
}


@pytest.fixture(scope="function")
def db():
    Base.metadata.create_all(bind=engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def client(db):
    def override_get_db():
        yield db

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


def create_task(client, **kwargs) -> dict:
    payload = {**TASK_PAYLOAD, **kwargs}
    res = client.post("/tasks", json=payload)
    assert res.status_code == 201, res.text
    return res.json()

