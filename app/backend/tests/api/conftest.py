import pytest
from fastapi.testclient import TestClient
from sqlalchemy import StaticPool, create_engine
from sqlalchemy.orm import Session, sessionmaker

from auth.jwt_auth import generate_access_token
from core.database import Base, get_db
from main import app
from tasks.models import TaskModel  # noqa: F401  (registers the table on Base.metadata)
from users.models import UsersModel

engine = create_engine(
    "sqlite:///:memory:",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

DEFAULT_PASSWORD = "12345678"


@pytest.fixture(autouse=True)
def db_session():
    """Fresh schema for every test so tests never depend on each other's data."""
    Base.metadata.create_all(bind=engine)
    session = TestSessionLocal()
    app.dependency_overrides[get_db] = lambda: session
    try:
        yield session
    finally:
        app.dependency_overrides.pop(get_db, None)
        session.close()
        Base.metadata.drop_all(bind=engine)


def create_user(session: Session, username: str, password: str = DEFAULT_PASSWORD) -> UsersModel:
    user = UsersModel(username=username)
    user.set_password(password)
    session.add(user)
    session.commit()
    session.refresh(user)
    return user


def client_for(user: UsersModel) -> TestClient:
    client = TestClient(app)
    client.headers["Authorization"] = f"Bearer {generate_access_token(user.id)}"
    return client


@pytest.fixture
def user(db_session):
    return create_user(db_session, "usertest")


@pytest.fixture
def other_user(db_session):
    return create_user(db_session, "otheruser")


@pytest.fixture
def anonymous_client():
    return TestClient(app)


@pytest.fixture
def auth_client(user):
    return client_for(user)


@pytest.fixture
def other_client(other_user):
    return client_for(other_user)
