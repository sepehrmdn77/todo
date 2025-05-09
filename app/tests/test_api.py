from fastapi.testclient import TestClient

from core.database import Base, create_engine, sessionmaker, get_db

from sqlalchemy import StaticPool

from main import app

SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool
)

TestSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    db = TestSessionLocal()

    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db

Base.metadata.create_all(bind=engine)

client = TestClient(app)


def test_login_response_401():
    payload = {"username": "test", "password": "1234567"}
    response = client.post("/users/login", json=payload)
    assert response.status_code == 401


# def test_login_response_200():
#     payload = {"username": "string", "password": "string"}
#     response = client.post("/users/login", json=payload)
#     assert response.status_code == 200
