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
    assert_error(client.post("/customers/search", json={"name": "a", "gender": "other"}), 400, "VALIDATION_ERROR")


def test_not_found(client):
    assert_error(client.put("/customers/999", json=make()), 404, "NOT_FOUND")
    assert_error(client.delete("/customers/999"), 404, "NOT_FOUND")


def test_unauthorized(client):
    assert_error(client.post("/customers/search", json={"name": "a"}, headers={"Authorization": ""}), 401, "UNAUTHORIZED")
    r = client.post("/customers", json=make(), headers={"Authorization": "Bearer wrong"})
    assert_error(r, 401, "UNAUTHORIZED")
    r = client.delete("/customers/1", headers={"Authorization": "Basic test-token"})
    assert_error(r, 401, "UNAUTHORIZED")


def test_unauthorized_when_token_not_set(client, monkeypatch):
    monkeypatch.delenv("API_TOKEN")
    assert_error(client.post("/customers/search", json={"name": "a"}), 401, "UNAUTHORIZED")


@pytest.mark.parametrize("cid", ["99999999999999999999", "0", "-1"])
def test_invalid_id_is_400(client, cid):
    assert_error(client.put(f"/customers/{cid}", json=make()), 400, "VALIDATION_ERROR")
    assert_error(client.delete(f"/customers/{cid}"), 400, "VALIDATION_ERROR")


@pytest.mark.parametrize("path", ["/docs", "/redoc", "/openapi.json"])
def test_docs_disabled(client, path):
    assert client.get(path).status_code == 404


def test_blank_name_is_400(client):
    assert_error(client.post("/customers", json=make(name="   ")), 400, "VALIDATION_ERROR")


def test_trailing_space_name_is_duplicate(client):
    assert client.post("/customers", json=make(name="山田 ")).status_code == 201
    assert_error(client.post("/customers", json=make(name="山田")), 409, "DUPLICATE")


@pytest.mark.parametrize("override", [
    {"name": "山\n田"},
    {"job": "営\t業"},
    {"name": "山\x07田"},
])
def test_control_chars_are_400(client, override):
    assert_error(client.post("/customers", json=make(**override)), 400, "VALIDATION_ERROR")
    cid = client.post("/customers", json=make()).json()["id"]
    assert_error(client.put(f"/customers/{cid}", json=make(**override)), 400, "VALIDATION_ERROR")


def test_search_control_chars_and_length_are_400(client):
    assert_error(client.post("/customers/search", json={"name": "a\nb"}), 400, "VALIDATION_ERROR")
    assert_error(client.post("/customers/search", json={"name": "a" * 257}), 400, "VALIDATION_ERROR")
