from conftest import make


def test_create_then_search(client):
    r = client.post("/customers", json=make())
    assert r.status_code == 201
    cid = r.json()["id"]
    found = client.get("/customers", params=make()).json()
    assert found == [{"id": cid, **make()}]


def test_job_optional_defaults_to_empty(client):
    client.post("/customers", json={"name": "a", "age": 1, "gender": "female"})
    found = client.get("/customers", params={"name": "a"}).json()
    assert found[0]["job"] == ""


def test_update_reflected(client):
    cid = client.post("/customers", json=make()).json()["id"]
    r = client.put(f"/customers/{cid}", json=make(name="花子", gender="female"))
    assert r.status_code == 204
    assert client.get("/customers", params={"name": "山田太郎"}).json() == []
    assert client.get("/customers", params={"name": "花子"}).json()[0]["gender"] == "female"


def test_delete(client):
    cid = client.post("/customers", json=make()).json()["id"]
    assert client.delete(f"/customers/{cid}").status_code == 204
    assert client.get("/customers", params=make()).json() == []


def test_search_no_condition_returns_empty(client):
    client.post("/customers", json=make())
    assert client.get("/customers").json() == []


def test_search_and_filter(client):
    client.post("/customers", json=make(name="a", age=20))
    client.post("/customers", json=make(name="a", age=30))
    client.post("/customers", json=make(name="b", age=30))
    assert len(client.get("/customers", params={"name": "a"}).json()) == 2
    assert len(client.get("/customers", params={"age": 30}).json()) == 2
    r = client.get("/customers", params={"name": "a", "age": 30}).json()
    assert len(r) == 1 and r[0]["name"] == "a" and r[0]["age"] == 30


def test_search_sql_injection_is_literal(client):
    client.post("/customers", json=make())
    assert client.get("/customers", params={"name": "' OR '1'='1"}).json() == []
