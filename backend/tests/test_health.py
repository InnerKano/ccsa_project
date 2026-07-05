def test_health_returns_healthy(client) -> None:
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}
