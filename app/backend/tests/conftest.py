import os

# Settings are read at import time; give the test process a self-contained configuration
# so tests never depend on (or touch) a developer's real database or secrets.
os.environ["SQLALCHEMY_DATABASE_URL"] = "sqlite:///:memory:"
os.environ["JWT_SECRET_KEY"] = "test-secret"
os.environ["CORS_ORIGINS"] = "[]"
