import os
from collections.abc import Generator

os.environ["DATABASE_URL"] = "sqlite:///./test_contract_os.db"
os.environ["ENVIRONMENT"] = "test"
os.environ["DEMO_MODE"] = "true"

import pytest
from app.database import Base, get_db
from app.main import app
from app.models import PlatformRole, User
from app.seed import seed
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session, sessionmaker

TEST_URL = "sqlite:///./test_contract_os.db"
engine = create_engine(TEST_URL, connect_args={"check_same_thread": False})
TestingSession = sessionmaker(bind=engine, expire_on_commit=False)


def override_db() -> Generator[Session, None, None]:
    with TestingSession() as session:
        yield session


@pytest.fixture(scope="session", autouse=True)
def database() -> Generator[None, None, None]:
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)
    seed()
    with TestingSession() as session:
        admin = session.scalar(select(User).where(User.email == "user-e3945303@example.test"))
        assert admin is not None
        admin.platform_role = PlatformRole.admin
        session.commit()
    yield
    Base.metadata.drop_all(engine)


@pytest.fixture
def client() -> Generator[TestClient, None, None]:
    with TestingSession() as session:
        admin = session.scalar(select(User).where(User.email == "user-e3945303@example.test"))
        assert admin is not None
        admin.platform_role = PlatformRole.admin
        session.commit()
    app.dependency_overrides[get_db] = override_db
    with TestClient(app, headers={"X-Demo-User": "user-d9853303@example.test"}) as value:
        yield value
    app.dependency_overrides.clear()
