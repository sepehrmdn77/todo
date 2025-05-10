from fastapi.testclient import TestClient

from core.database import Base, create_engine, sessionmaker, get_db

from sqlalchemy import StaticPool

from main import app

import pytest

from faker import Faker

from users.models import UsersModel

from tasks.models import TaskModel

fake = Faker()

SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool
)

TestSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

#  module
@pytest.fixture(scope="module")
def db_session():
    db = TestSessionLocal()

    try:
        yield db
    finally:
        db.close()


#  module
@pytest.fixture(scope="module", autouse=True)
def override_dependencies(db_session):

    app.dependency_overrides[get_db] = lambda: db_session
    yield
    app.dependency_overrides.pop(get_db,None)


#  session
@pytest.fixture(scope="session", autouse=True)
def tearup_and_down_db():
    '''export env variables in test env:
    export SQLALCHEMY_DATABASE_URL="sqlite:///:memory:"
    export JWT_SECRET_KEY="test"'''
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


#  function
@pytest.fixture(scope="function")
def anonymous_client():
    client = TestClient(app)
    yield client


#  module
@pytest.fixture(scope="module", autouse=True)
def generate_mock_data(db_session):
    user = UsersModel(username="usertest")
    user.set_password("12345678")
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    print(f"user created with username: {user.username} and ID: {user.id}")

    task_list = []
    for _ in range(10):
        task_list.append(
            TaskModel(
                user_id=user.id,
                title=fake.sentence(nb_words=6),
                description=fake.text(),
                is_completed=fake.boolean(),
            )
        )
    db_session.add_all(task_list)
    db_session.commit()
    print(f"added 10 tasks for user id: {user.id}")

