"""Statements API happy-path, isolation, and error tests."""

import pytest
from fastapi.testclient import TestClient

from app.modules.statements.tests.conftest import SAMPLE_CSV

pytestmark = pytest.mark.integration


def test_upload_statement_persists_transactions(
    client: TestClient, auth_headers: dict[str, str]
) -> None:
    with SAMPLE_CSV.open("rb") as csv_file:
        response = client.post(
            "/api/statements",
            files={"file": ("sample.csv", csv_file, "text/csv")},
            headers=auth_headers,
        )
    assert response.status_code == 201
    body = response.json()
    assert body["filename"] == "sample.csv"
    assert body["currency"] == "USD"
    assert body["transaction_count"] == 9
    assert "id" in body
    assert "uploaded_at" in body


def test_list_statements_returns_metadata_only(
    client: TestClient, auth_headers: dict[str, str]
) -> None:
    with SAMPLE_CSV.open("rb") as csv_file:
        upload = client.post(
            "/api/statements",
            files={"file": ("march.csv", csv_file, "text/csv")},
            headers=auth_headers,
        )
    assert upload.status_code == 201

    response = client.get("/api/statements", headers=auth_headers)
    assert response.status_code == 200
    items = response.json()
    assert len(items) >= 1
    assert "transactions" not in items[0]
    assert items[0]["filename"] == "march.csv"


def test_get_statement_includes_transactions(
    client: TestClient, auth_headers: dict[str, str]
) -> None:
    with SAMPLE_CSV.open("rb") as csv_file:
        upload = client.post(
            "/api/statements",
            files={"file": ("detail.csv", csv_file, "text/csv")},
            headers=auth_headers,
        )
    statement_id = upload.json()["id"]

    response = client.get(f"/api/statements/{statement_id}", headers=auth_headers)
    assert response.status_code == 200
    body = response.json()
    assert body["id"] == statement_id
    assert len(body["transactions"]) == 9
    first = body["transactions"][0]
    assert {"id", "date", "description", "amount", "category"} <= first.keys()
    assert first["category"] is None


def test_delete_statement_returns_204(
    client: TestClient, auth_headers: dict[str, str]
) -> None:
    with SAMPLE_CSV.open("rb") as csv_file:
        upload = client.post(
            "/api/statements",
            files={"file": ("delete-me.csv", csv_file, "text/csv")},
            headers=auth_headers,
        )
    statement_id = upload.json()["id"]

    delete = client.delete(f"/api/statements/{statement_id}", headers=auth_headers)
    assert delete.status_code == 204

    get_after = client.get(f"/api/statements/{statement_id}", headers=auth_headers)
    assert get_after.status_code == 404


def test_other_user_cannot_access_statement(
    client: TestClient,
    auth_headers: dict[str, str],
    other_user_headers: dict[str, str],
) -> None:
    with SAMPLE_CSV.open("rb") as csv_file:
        upload = client.post(
            "/api/statements",
            files={"file": ("private.csv", csv_file, "text/csv")},
            headers=auth_headers,
        )
    statement_id = upload.json()["id"]

    response = client.get(f"/api/statements/{statement_id}", headers=other_user_headers)
    assert response.status_code == 404


def test_upload_without_auth_returns_401(client: TestClient) -> None:
    with SAMPLE_CSV.open("rb") as csv_file:
        response = client.post(
            "/api/statements",
            files={"file": ("sample.csv", csv_file, "text/csv")},
        )
    assert response.status_code == 401


def test_upload_invalid_csv_returns_400(
    client: TestClient, auth_headers: dict[str, str]
) -> None:
    response = client.post(
        "/api/statements",
        files={"file": ("bad.csv", b"not,a,valid\n", "text/csv")},
        headers=auth_headers,
    )
    assert response.status_code == 400
    assert "detail" in response.json()


def test_upload_custom_column_mapping(
    client: TestClient, auth_headers: dict[str, str]
) -> None:
    custom_csv = b"Transaction Date,Memo,Debit\n03/15/2026,COFFEE SHOP,4.50\n"
    response = client.post(
        "/api/statements",
        files={"file": ("custom.csv", custom_csv, "text/csv")},
        data={
            "date_column": "Transaction Date",
            "description_column": "Memo",
            "amount_column": "Debit",
        },
        headers=auth_headers,
    )
    assert response.status_code == 201
    assert response.json()["transaction_count"] == 1
