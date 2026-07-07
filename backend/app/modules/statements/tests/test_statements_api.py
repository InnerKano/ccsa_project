"""Statements API happy-path, isolation, and error tests."""

import pytest
from fastapi.testclient import TestClient

from app.modules.statements.tests.conftest import SAMPLE_CSV, SAMPLE_ES_CSV

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
    assert body["transaction_count"] == 19
    assert "id" in body
    assert "uploaded_at" in body


def test_upload_spanish_latam_statement(
    client: TestClient, auth_headers: dict[str, str]
) -> None:
    with SAMPLE_ES_CSV.open("rb") as csv_file:
        response = client.post(
            "/api/statements",
            files={"file": ("sample_es.csv", csv_file, "text/csv")},
            data={"currency": "COP"},
            headers=auth_headers,
        )
    assert response.status_code == 201
    body = response.json()
    assert body["currency"] == "COP"
    assert body["transaction_count"] == 15


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
    assert len(body["transactions"]) == 19
    first = body["transactions"][0]
    assert {"id", "date", "description", "amount", "category"} <= first.keys()
    assert first["category"] is None


def _upload(client: TestClient, auth_headers: dict[str, str], name: str) -> str:
    with SAMPLE_CSV.open("rb") as csv_file:
        upload = client.post(
            "/api/statements",
            files={"file": (name, csv_file, "text/csv")},
            headers=auth_headers,
        )
    assert upload.status_code == 201
    return upload.json()["id"]


def test_archive_statement_hides_it_from_owner(
    client: TestClient, auth_headers: dict[str, str]
) -> None:
    statement_id = _upload(client, auth_headers, "archive-me.csv")

    # DELETE is a soft archive (D22): 204, then hidden from reads and the list.
    archive = client.delete(f"/api/statements/{statement_id}", headers=auth_headers)
    assert archive.status_code == 204

    get_after = client.get(f"/api/statements/{statement_id}", headers=auth_headers)
    assert get_after.status_code == 404

    listed = client.get("/api/statements", headers=auth_headers)
    assert all(item["id"] != statement_id for item in listed.json())


def test_archived_statement_listed_only_in_archived_view(
    client: TestClient, auth_headers: dict[str, str]
) -> None:
    statement_id = _upload(client, auth_headers, "archived-view.csv")
    client.delete(f"/api/statements/{statement_id}", headers=auth_headers)

    active = client.get("/api/statements", headers=auth_headers).json()
    assert all(item["id"] != statement_id for item in active)

    archived = client.get("/api/statements?archived=true", headers=auth_headers)
    assert archived.status_code == 200
    match = [item for item in archived.json() if item["id"] == statement_id]
    assert len(match) == 1
    assert match[0]["deleted_at"] is not None

    # Restoring empties the archived view again.
    client.post(f"/api/statements/{statement_id}/restore", headers=auth_headers)
    archived_after = client.get("/api/statements?archived=true", headers=auth_headers).json()
    assert all(item["id"] != statement_id for item in archived_after)


def test_restore_statement_makes_it_visible_again(
    client: TestClient, auth_headers: dict[str, str]
) -> None:
    statement_id = _upload(client, auth_headers, "restore-me.csv")

    assert (
        client.delete(f"/api/statements/{statement_id}", headers=auth_headers).status_code
        == 204
    )

    restore = client.post(
        f"/api/statements/{statement_id}/restore", headers=auth_headers
    )
    assert restore.status_code == 200
    assert restore.json()["id"] == statement_id

    get_after = client.get(f"/api/statements/{statement_id}", headers=auth_headers)
    assert get_after.status_code == 200


def test_archived_statement_analyses_are_hidden_and_restored(
    client: TestClient, auth_headers: dict[str, str]
) -> None:
    statement_id = _upload(client, auth_headers, "analyzed.csv")

    analysis = client.post(f"/api/analysis/{statement_id}", headers=auth_headers)
    assert analysis.status_code == 201
    analysis_id = analysis.json()["id"]

    client.delete(f"/api/statements/{statement_id}", headers=auth_headers)
    # Derived analyses of an archived statement are hidden alongside it (D22).
    assert client.get("/api/analysis", headers=auth_headers).json() == []
    assert client.get(f"/api/analysis/{analysis_id}", headers=auth_headers).status_code == 404

    client.post(f"/api/statements/{statement_id}/restore", headers=auth_headers)
    assert client.get(f"/api/analysis/{analysis_id}", headers=auth_headers).status_code == 200


def test_permanent_delete_erases_statement(
    client: TestClient, auth_headers: dict[str, str]
) -> None:
    statement_id = _upload(client, auth_headers, "erase-me.csv")

    permanent = client.delete(
        f"/api/statements/{statement_id}/permanent", headers=auth_headers
    )
    assert permanent.status_code == 204

    # Gone for good — not even restorable.
    assert (
        client.post(f"/api/statements/{statement_id}/restore", headers=auth_headers).status_code
        == 404
    )


def test_other_user_cannot_archive_statement(
    client: TestClient,
    auth_headers: dict[str, str],
    other_user_headers: dict[str, str],
) -> None:
    statement_id = _upload(client, auth_headers, "mine.csv")

    response = client.delete(
        f"/api/statements/{statement_id}", headers=other_user_headers
    )
    assert response.status_code == 404
    # Still visible to the real owner.
    assert client.get(f"/api/statements/{statement_id}", headers=auth_headers).status_code == 200


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
