"""Analysis API happy-path, persistence, isolation, and error tests."""

import pytest
from fastapi.testclient import TestClient

pytestmark = pytest.mark.integration


def test_analyze_statement_detects_subscriptions(
    client: TestClient, auth_headers: dict[str, str], statement_id: str
) -> None:
    response = client.post(f"/api/analysis/{statement_id}", headers=auth_headers)
    assert response.status_code == 201
    body = response.json()

    assert body["statement_id"] == statement_id
    assert body["ai_enabled"] is False  # rules-only in the MVP (D2)
    assert body["monthly_recurring_total"] == "41.47"
    assert body["estimated_savings"] == "26.48"

    merchants = {s["merchant"] for s in body["detected_subscriptions"]}
    assert merchants == {"NETFLIX", "SPOTIFY", "AMAZON PRIME"}
    assert len(body["recommendations"]) == 2

    comparison = body["spending_comparison"]
    before = {s["category"]: s["amount"] for s in comparison["before"]}
    after = {s["category"]: s["amount"] for s in comparison["after"]}
    assert before == {
        "streaming": "15.49",
        "shopping": "14.99",
        "music": "10.99",
    }
    assert after == {
        "shopping": "14.99",
        "streaming": "0.00",
        "music": "0.00",
    }


def test_analysis_is_persisted_and_retrievable(
    client: TestClient, auth_headers: dict[str, str], statement_id: str
) -> None:
    created = client.post(f"/api/analysis/{statement_id}", headers=auth_headers)
    analysis_id = created.json()["id"]

    detail = client.get(f"/api/analysis/{analysis_id}", headers=auth_headers)
    assert detail.status_code == 200
    assert detail.json()["id"] == analysis_id
    assert len(detail.json()["detected_subscriptions"]) == 3

    listing = client.get("/api/analysis", headers=auth_headers)
    assert listing.status_code == 200
    items = listing.json()
    assert any(item["id"] == analysis_id for item in items)
    assert "detected_subscriptions" not in items[0]  # summary view only


def test_reanalysis_appends_new_row(
    client: TestClient, auth_headers: dict[str, str], statement_id: str
) -> None:
    first = client.post(f"/api/analysis/{statement_id}", headers=auth_headers)
    second = client.post(f"/api/analysis/{statement_id}", headers=auth_headers)
    assert first.json()["id"] != second.json()["id"]  # D10 — appended, not replaced

    listing = client.get("/api/analysis", headers=auth_headers).json()
    for_statement = [a for a in listing if a["statement_id"] == statement_id]
    assert len(for_statement) == 2


def test_analysis_categorizes_transactions(
    client: TestClient, auth_headers: dict[str, str], statement_id: str
) -> None:
    client.post(f"/api/analysis/{statement_id}", headers=auth_headers)

    detail = client.get(f"/api/statements/{statement_id}", headers=auth_headers).json()
    categories = {tx["description"]: tx["category"] for tx in detail["transactions"]}
    assert categories["NETFLIX.COM"] == "streaming"
    assert categories["PAYROLL DEPOSIT"] == "income"


def test_analyze_nonexistent_statement_returns_404(
    client: TestClient, auth_headers: dict[str, str]
) -> None:
    missing = "00000000-0000-0000-0000-000000000000"
    response = client.post(f"/api/analysis/{missing}", headers=auth_headers)
    assert response.status_code == 404


def test_other_user_cannot_analyze_or_read(
    client: TestClient,
    auth_headers: dict[str, str],
    other_user_headers: dict[str, str],
    statement_id: str,
) -> None:
    # Another user cannot analyze a statement they do not own.
    forbidden = client.post(f"/api/analysis/{statement_id}", headers=other_user_headers)
    assert forbidden.status_code == 404

    created = client.post(f"/api/analysis/{statement_id}", headers=auth_headers)
    analysis_id = created.json()["id"]

    # ...nor read the resulting analysis.
    response = client.get(f"/api/analysis/{analysis_id}", headers=other_user_headers)
    assert response.status_code == 404


def test_analysis_requires_auth(client: TestClient, statement_id: str) -> None:
    assert client.post(f"/api/analysis/{statement_id}").status_code == 401
    assert client.get("/api/analysis").status_code == 401
