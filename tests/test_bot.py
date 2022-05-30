# mypy: no-disallow-untyped-decorators
# pylint: disable=E0611,E0401


import pytest
from fastapi.testclient import TestClient
from main import app
from models.bot import BotModel
from sqlmodel import SQLModel, Session, create_engine
from sqlmodel.pool import StaticPool
from db import get_session


@pytest.fixture(name="session")
def session_fixture():
    engine = create_engine(
        "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool
    )
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        yield session


@pytest.fixture(name="client")  #
def client_fixture(session: Session):  #
    def get_session_override():  #
        return session

    app.dependency_overrides[get_session] = get_session_override  #
    client = TestClient(app)  #
    yield client  #
    app.dependency_overrides.clear()


def test_database_is_empty(client: TestClient):  # nosec
    response = client.get("/api/bots/")
    assert response.status_code == 200, response.text
    data = response.json([])


def test_create_dummy_bot_1(client: TestClient):  # nosec
    response = client.post(
        "/api/bots/",
        json={
            "name": "dummy bot 1",
            "description": "dummy bot 1",
            "exchange_account": "binance_main_account",
            "symbol": "BTC/USDT",
            "amount": 0.01,
            "buy_up_levels": 2,
            "buy_down_levels": 3,
            "level_percent": 1.0,
        },
    )
    assert response.status_code == 200, response.text
    data = response.json()
    assert data["name"] == "dummy bot 1"
