from sqlalchemy import (
    Column,
    String,
    Integer,
    ForeignKey,
    Boolean,
    # Text,
    func,
    DateTime,
)
from sqlalchemy.orm import relationship
from core.database import Base
from passlib.context import CryptContext

pwd_context = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto"
)


class UsersModel(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, autoincrement=True)

    username = Column(String(250), nullable=False)
    password = Column(String, nullable=False)

    is_active = Column(Boolean, default=True)

    created_date = Column(DateTime, server_default=func.now(), nullable=False)
    updated_date = Column(
        DateTime, server_default=func.now(), server_onupdate=func.now(), nullable=False
    )

    tasks = relationship("TaskModel", back_populates="user")

    def hash_password(self, plain_password: str) -> str:
        """Hashing password"""
        return pwd_context.hash(plain_password)

    def verify_password(self, plain_password: str) -> bool:
        """Verifying password"""
        return pwd_context.verify(plain_password, self.password)

    def set_password(self, plain_text: str) -> None:
        self.password = self.hash_password(plain_text)


class TokenModel(Base):
    __tablename__ = "tokens"

    user_id = Column(Integer, ForeignKey("users.id"))
    id = Column(Integer, primary_key=True, autoincrement=True)
    token = Column(String, nullable=False)
    created_date = Column(DateTime, server_default=func.now())

    user = relationship("UsersModel", uselist=False)
