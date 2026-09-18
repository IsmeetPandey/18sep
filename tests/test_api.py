from pathlib import Path

from fastapi.testclient import TestClient


def test_health_and_idempotent_ingestion(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("SIGNALDESK_DB", str(tmp_path / "test.db"))
    import app.main as main

    main.DB_PATH = str(tmp_path / "test.db")
    main.API_KEY = None
    with TestClient(main.app) as client:
        assert client.get("/health").json() == {"status": "ok"}
        payload = {
            "provider": "demo",
            "provider_event_id": "evt-1",
            "author": "customer-1",
            "body": "I want a quote for the team plan",
            "reach": 100,
        }
        first = client.post("/interactions", json=payload)
        second = client.post("/interactions", json=payload)
        assert first.status_code == 201
        assert second.status_code == 201
        assert first.json()["id"] == second.json()["id"]


def test_invalid_transition_returns_conflict(tmp_path: Path) -> None:
    import app.main as main

    main.DB_PATH = str(tmp_path / "test.db")
    main.API_KEY = None
    with TestClient(main.app) as client:
        created = client.post(
            "/interactions",
            json={"provider": "demo", "provider_event_id": "evt-2", "author": "a", "body": "hello"},
        ).json()
        interaction_id = created["id"]
        assert client.patch(f"/interactions/{interaction_id}/status", json={"status": "resolved"}).status_code == 200
        assert client.patch(f"/interactions/{interaction_id}/status", json={"status": "open"}).status_code == 409


def test_write_requires_api_key_when_configured(tmp_path: Path) -> None:
    import app.main as main

    main.DB_PATH = str(tmp_path / "test.db")
    main.API_KEY = "test-secret"
    with TestClient(main.app) as client:
        response = client.post(
            "/interactions",
            json={"provider": "demo", "provider_event_id": "evt-3", "author": "a", "body": "hello"},
        )
        assert response.status_code == 401
        authorized = client.post(
            "/interactions",
            headers={"X-API-Key": "test-secret"},
            json={"provider": "demo", "provider_event_id": "evt-3", "author": "a", "body": "hello"},
        )
        assert authorized.status_code == 201
