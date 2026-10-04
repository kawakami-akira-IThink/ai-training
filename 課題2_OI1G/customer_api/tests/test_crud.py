from conftest import make


def test_create_then_search(client):
    r = client.post("/customers", json=make())
    assert r.status_code == 201
    cid = r.json()["id"]
    found = client.post("/customers/search", json=make()).json()
    assert found == [{"id": cid, **make()}]


def test_job_optional_defaults_to_empty(client):
    client.post("/customers", json={"name": "a", "age": 1, "gender": "female"})
    found = client.post("/customers/search", json={"name": "a"}).json()
    assert found[0]["job"] == ""


def test_update_reflected(client):
    cid = client.post("/customers", json=make()).json()["id"]
    r = client.put(f"/customers/{cid}", json=make(name="花子", gender="female"))
    assert r.status_code == 204
    assert client.post("/customers/search", json={"name": "山田太郎"}).json() == []
    assert client.post("/customers/search", json={"name": "花子"}).json()[0]["gender"] == "female"


def test_delete(client):
    cid = client.post("/customers", json=make()).json()["id"]
    assert client.delete(f"/customers/{cid}").status_code == 204
    assert client.post("/customers/search", json=make()).json() == []


def test_search_without_name_is_400(client):
    client.post("/customers", json=make())
    for body in ({}, {"gender": "male"}, {"age": 30}, {"name": "   "}):
        r = client.post("/customers/search", json=body)
        assert r.status_code == 400 and r.json()["code"] == "VALIDATION_ERROR"


def test_search_name_and_gender_and(client):
    client.post("/customers", json=make(name="a", gender="male"))
    client.post("/customers", json=make(name="a", gender="female"))
    client.post("/customers", json=make(name="b", gender="female"))
    r = client.post("/customers/search", json={"name": "a", "gender": "female"}).json()
    assert len(r) == 1 and r[0]["name"] == "a" and r[0]["gender"] == "female"


def test_search_name_is_stripped(client):
    client.post("/customers", json=make(name="山田"))
    assert len(client.post("/customers/search", json={"name": " 山田 "}).json()) == 1


def test_get_search_endpoint_removed(client):
    assert client.get("/customers", params={"name": "a"}).status_code == 405


def test_search_and_filter(client):
    client.post("/customers", json=make(name="a", age=20))
    client.post("/customers", json=make(name="a", age=30))
    client.post("/customers", json=make(name="b", age=30))
    assert len(client.post("/customers/search", json={"name": "a"}).json()) == 2
    r = client.post("/customers/search", json={"name": "a", "age": 30}).json()
    assert len(r) == 1 and r[0]["name"] == "a" and r[0]["age"] == 30


def test_search_sql_injection_is_literal(client):
    client.post("/customers", json=make())
    assert client.post("/customers/search", json={"name": "' OR '1'='1"}).json() == []
