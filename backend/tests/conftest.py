import pytest

from app.main import create_app


@pytest.fixture()
def app(tmp_path):
    return create_app(start_services=False, settings_path=tmp_path / "settings.json")


@pytest.fixture()
def client(app):
    from fastapi.testclient import TestClient

    with TestClient(app) as c:
        yield c
