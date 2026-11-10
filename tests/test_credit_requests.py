import pytest
from fastapi.testclient import TestClient

from app.main import app, store

client = TestClient(app)

URL = "/credit-requests"
BODY = {"lender_id": "LENDER-1", "borrower_ref": "BORROWER-1", "loan_amount": 50000}


@pytest.fixture(autouse=True)
def clear_store():
    store.clear()
    yield
    store.clear()


def post(body: dict, key: str | None):
    headers = {"Idempotency-Key": key} if key is not None else {}
    return client.post(URL, json=body, headers=headers)


def test_first_post_returns_201_and_id():
    resp = post(BODY, "key-aaaa-0001")

    assert resp.status_code == 201
    data = resp.json()
    assert data["id"]
    assert data["loan_amount"] == BODY["loan_amount"]


def test_same_key_same_body_returns_same_id_with_200():
    first = post(BODY, "key-aaaa-0001")
    second = post(BODY, "key-aaaa-0001")

    assert first.status_code == 201
    assert second.status_code == 200
    assert second.json()["id"] == first.json()["id"]
    assert len(store) == 1


def test_same_key_different_loan_amount_returns_409():
    first = post(BODY, "key-aaaa-0001")
    second = post({**BODY, "loan_amount": 99999}, "key-aaaa-0001")

    assert first.status_code == 201
    assert second.status_code == 409


def test_missing_idempotency_key_returns_422():
    resp = post(BODY, None)

    assert resp.status_code == 422
    assert len(store) == 0


def test_different_keys_create_different_requests():
    first = post(BODY, "key-aaaa-0001")
    second = post(BODY, "key-bbbb-0002")

    assert first.status_code == 201
    assert second.status_code == 201
    assert first.json()["id"] != second.json()["id"]
    assert len(store) == 2
