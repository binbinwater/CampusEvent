import uuid
from pathlib import Path

import pytest

from campusevent import create_app
from campusevent.db import get_db

RUNTIME_DIR = Path(__file__).resolve().parent / "_runtime"
FIXED_NOW = "2026-11-19T10:00:00"
DEFAULT_PASSWORD = {
    "student_a": "student123",
    "student_b": "student123",
    "student_c": "student123",
    "admin": "admin123",
}


@pytest.fixture
def db_path():
    RUNTIME_DIR.mkdir(parents=True, exist_ok=True, mode=0o777)
    path = RUNTIME_DIR / f"campusevent-{uuid.uuid4().hex}.sqlite3"
    yield path
    for suffix in ("", "-wal", "-shm"):
        candidate = Path(str(path) + suffix)
        if candidate.exists():
            candidate.unlink()


@pytest.fixture
def app(db_path):
    application = create_app(
        {
            "TESTING": True,
            "DATABASE": str(db_path),
            "SECRET_KEY": "test-secret",
            "NOW_OVERRIDE": FIXED_NOW,
        }
    )
    yield application


@pytest.fixture
def login():
    def _login(client, username):
        password = DEFAULT_PASSWORD[username]
        response = client.post(
            "/login",
            data={"username": username, "password": password},
            follow_redirects=True,
        )
        assert response.status_code == 200
        assert "活动列表" in response.get_data(as_text=True)
        return client

    return _login


@pytest.fixture
def admin_client(app, login):
    return login(app.test_client(), "admin")


@pytest.fixture
def student_a(app, login):
    return login(app.test_client(), "student_a")


@pytest.fixture
def student_b(app, login):
    return login(app.test_client(), "student_b")


@pytest.fixture
def student_c(app, login):
    return login(app.test_client(), "student_c")


@pytest.fixture
def create_activity(admin_client):
    def _create(
        *,
        title="迎新志愿活动",
        category="志愿服务",
        start_at="2026-11-21T14:00",
        location="大学生活动中心",
        capacity=2,
        policy_type="direct",
        follow_redirects=False,
    ):
        response = admin_client.post(
            "/activities/new",
            data={
                "title": title,
                "category": category,
                "start_at": start_at,
                "location": location,
                "capacity": str(capacity),
                "policy_type": policy_type,
            },
            follow_redirects=follow_redirects,
        )
        assert response.status_code in (200, 303), response.get_data(as_text=True)
        if response.status_code == 303:
            location = response.headers["Location"]
            return int(location.rstrip("/").split("/")[-1])
        return None

    return _create


@pytest.fixture
def fetch_one(app):
    def _fetch_one(sql, parameters=()):
        with app.app_context():
            return get_db().execute(sql, parameters).fetchone()

    return _fetch_one


@pytest.fixture
def count_rows(app):
    def _count(table, where="", parameters=()):
        sql = f"SELECT COUNT(*) AS n FROM {table}"
        if where:
            sql += " WHERE " + where
        with app.app_context():
            return get_db().execute(sql, parameters).fetchone()["n"]

    return _count