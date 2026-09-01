import os
import tempfile
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

os.environ.setdefault("REFERENCE_JSON_PATH", os.path.join(os.path.dirname(__file__), "..", "..", "data", "reference.json"))

from app.database import Base, get_db
from app import models
from app.auth import hash_password
from app.main import app
from app import storage as storage_module


@pytest.fixture()
def tmp_storage_path(tmp_path, monkeypatch):
    monkeypatch.setenv("STORAGE_LOCAL_PATH", str(tmp_path))
    storage_module._instance = storage_module.LocalDiskStorage(str(tmp_path))
    yield tmp_path
    storage_module._instance = None


@pytest.fixture()
def db_session(tmp_storage_path):
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,  # keep a single connection so the in-memory DB persists across the session
    )
    Base.metadata.create_all(bind=engine)
    TestingSessionLocal = sessionmaker(bind=engine)
    session = TestingSessionLocal()

    def override_get_db():
        try:
            yield session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    yield session
    session.close()
    app.dependency_overrides.clear()


@pytest.fixture()
def client(db_session):
    return TestClient(app)


@pytest.fixture()
def editor_token(db_session, client):
    db_session.add(models.User(email="editor@test.io", hashed_password=hash_password("pw"), role=models.Role.editor))
    db_session.commit()
    r = client.post("/auth/login", json={"email": "editor@test.io", "password": "pw"})
    return r.json()["access_token"]


@pytest.fixture()
def admin_token(db_session, client):
    db_session.add(models.User(email="admin@test.io", hashed_password=hash_password("pw"), role=models.Role.admin))
    db_session.commit()
    r = client.post("/auth/login", json={"email": "admin@test.io", "password": "pw"})
    return r.json()["access_token"]


def auth_headers(token):
    return {"Authorization": f"Bearer {token}"}
