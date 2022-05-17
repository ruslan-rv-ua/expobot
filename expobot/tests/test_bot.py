# mypy: no-disallow-untyped-decorators
# pylint: disable=E0611,E0401
import asyncio
from typing import Generator

import pytest
from fastapi.testclient import TestClient
from main import app
from models.bot import BotModel

from tortoise.contrib.test import finalizer, initializer


@pytest.fixture(scope="module")
def client() -> Generator:
    initializer(["models"])
    with TestClient(app) as client:
        yield client
    finalizer()


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
