from pathlib import Path

import pytest
from starlette.testclient import TestClient

from web.app import create_app


def test_the_token_link_signs_the_browser_in(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.chdir(tmp_path)
    client = TestClient(create_app(token="secret-token"))
    assert client.get("/api/home").status_code == 401
    signed = client.get("/?token=secret-token", follow_redirects=False)
    assert signed.status_code == 303
    assert "httponly" in signed.headers["set-cookie"].lower()
    assert client.get("/api/home").status_code == 200


def test_a_wrong_token_link_is_refused(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.chdir(tmp_path)
    client = TestClient(create_app(token="secret-token"))
    assert client.get("/?token=guess", follow_redirects=False).status_code == 401
    assert client.get("/api/home").status_code == 401


def test_not_found_hides_filesystem_paths(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.chdir(tmp_path)
    response = TestClient(create_app()).get("/api/files/inbox/deadbeef/meta")
    assert response.status_code == 404
    assert str(tmp_path) not in response.text
