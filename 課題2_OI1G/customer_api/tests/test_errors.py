import pytest

from conftest import make


def assert_error(r, status, code):
    assert r.status_code == status
    body = r.json()
    assert body["code"] == code and "message" in body


def test_duplicate_create(client):
    client.post("/customers", json=make())
    assert_error(client.post("/customers", json=make()), 409, "DUPLICATE")


def test_duplicate_create_with_empty_job(client):
    body = {"name": "a", "age": 1, "gender": "male"}
    client.post("/customers", json=body)
    assert_error(client.post("/customers", json=body), 409, "DUPLICATE")


def test_duplicate_update(client):
    client.post("/customers", json=make(name="a"))
    cid = client.post("/customers", json=make(name="b")).json()["id"]
    assert_error(client.put(f"/customers/{cid}", json=make(name="a")), 409, "DUPLICATE")


def test_update_to_same_content_is_ok(client):
    cid = client.post("/customers", json=make()).json()["id"]
    assert client.put(f"/customers/{cid}", json=make()).status_code == 204


@pytest.mark.parametrize("override", [
    {"name": ""},
    {"name": "a" * 257},
    {"age": -1},
    {"age": 1001},
    {"age": "abc"},
    {"gender": "other"},
    {"job": "a" * 257},
])
def test_validation_error(client, override):
    assert_error(client.post("/customers", json=make(**override)), 400, "VALIDATION_ERROR")


def test_missing_required_field(client):
    assert_error(client.post("/customers", json={"name": "a"}), 400, "VALIDATION_ERROR")


def test_validation_boundaries_ok(client):
    assert client.post("/customers", json=make(name="a" * 256, age=0, job="b" * 256)).status_code == 201
    assert client.post("/customers", json=make(name="c", age=1000, gender="female", job="")).status_code == 201


def test_validation_error_on_update_and_search(client):
    cid = client.post("/customers", json=make()).json()["id"]
    assert_error(client.put(f"/customers/{cid}", json=make(age=1001)), 400, "VALIDATION_ERROR")
    assert_error(client.get("/customers", params={"gender": "other"}), 400, "VALIDATION_ERROR")


def test_not_found(client):
    assert_error(client.put("/customers/999", json=make()), 404, "NOT_FOUND")
    assert_error(client.delete("/customers/999"), 404, "NOT_FOUND")


def test_unauthorized(client):
    assert_error(client.get("/customers", params={"name": "a"}, headers={"Authorization": ""}), 401, "UNAUTHORIZED")
    r = client.post("/customers", json=make(), headers={"Authorization": "Bearer wrong"})
    assert_error(r, 401, "UNAUTHORIZED")
    r = client.delete("/customers/1", headers={"Authorization": "Basic test-token"})
    assert_error(r, 401, "UNAUTHORIZED")


def test_unauthorized_when_token_not_set(client, monkeypatch):
    monkeypatch.delenv("API_TOKEN")
    assert_error(client.get("/customers", params={"name": "a"}), 401, "UNAUTHORIZED")
