import os
from pathlib import Path
import sys

import pytest
from fastapi.testclient import TestClient

os.environ["DATABASE_URL"] = "sqlite:///./test_privacyops.db"
os.environ["JWT_SECRET"] = "test-secret"
os.environ["UPLOAD_DIR"] = "test_uploads"

BASE_DIR = Path(__file__).resolve().parents[1]
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from app.database import Base, engine  # noqa: E402
from app.main import app  # noqa: E402


@pytest.fixture(autouse=True)
def reset_db():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    yield


@pytest.fixture(autouse=True)
def reset_storage():
    for folder in ["test_uploads", "exports", "test_exports"]:
        path = Path(folder)
        if path.exists():
            for child in path.rglob("*"):
                if child.is_file():
                    child.unlink()
            for child in sorted(path.rglob("*"), reverse=True):
                if child.is_dir():
                    child.rmdir()
            path.rmdir()
    yield


@pytest.fixture
def client():
    with TestClient(app) as c:
        yield c
