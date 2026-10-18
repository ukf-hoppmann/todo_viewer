from __future__ import annotations

import logging

import pytest
from fastapi import FastAPI
from starlette.testclient import TestClient


def test_browser_entry_lands_in_the_server_log(app: FastAPI, caplog: pytest.LogCaptureFixture) -> None:
    with caplog.at_level(logging.INFO), TestClient(app) as c:
        response = c.post(
            "/api/core/client-log",
            json={
                "level": "error",
                "origin": "core",
                "id": "a1b2c3d4",
                "message": "errors.unexpected",
                "session_id": "s1",
            },
        )

    assert response.json() == {"accepted": True}
    records = [r for r in caplog.records if r.name == "viewer.client"]
    assert len(records) == 1 and records[0].levelno == logging.ERROR
    assert "a1b2c3d4" in str(records[0].msg)


def test_invalid_level_is_a_client_error(app: FastAPI) -> None:
    with TestClient(app) as c:
        response = c.post("/api/core/client-log", json={"level": "fatal"})

    assert response.status_code == 400 or response.status_code == 422
