from conftest import make


def test_locked_on_create_update_delete(client, lock_db):
    r = client.post("/customers", json=make())
    assert r.status_code == 409 and r.json()["code"] == "LOCKED"
    r = client.put("/customers/1", json=make())
    assert r.status_code == 409 and r.json()["code"] == "LOCKED"
    r = client.delete("/customers/1")
    assert r.status_code == 409 and r.json()["code"] == "LOCKED"


def test_search_works_while_locked(client, lock_db):
    assert client.post("/customers/search", json={"name": "x"}).status_code == 200


def test_works_again_after_unlock(client, lock_db):
    assert client.post("/customers", json=make()).status_code == 409
    lock_db.execute("ROLLBACK")
    assert client.post("/customers", json=make()).status_code == 201
