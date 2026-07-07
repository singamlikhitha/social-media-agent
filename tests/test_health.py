"""Smoke tests for the health endpoints.

These verify the app boots (imports + routes wire up) and the health router
responds — a cheap gate that catches import-time regressions in CI.
"""


def test_health_ok(client):
    resp = client.get("/api/health")
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "healthy"
    assert body["service"]
    assert body["version"]


def test_health_trailing_slash(client):
    # Router registers both "" and "/" — both should resolve.
    resp = client.get("/api/health/")
    assert resp.status_code == 200
    assert resp.json()["status"] == "healthy"


def test_health_config(client):
    resp = client.get("/api/health/config")
    assert resp.status_code == 200
    body = resp.json()
    # Structural check — values depend on env, keys must always be present.
    for key in ("gemini_configured", "meta_configured", "google_configured", "database", "timezone"):
        assert key in body
