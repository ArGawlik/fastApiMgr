from fastapi.testclient import TestClient
from main import app
from datetime import datetime, timedelta
from main import Patient, PatientInfo
import sqlite3

client = TestClient(app)


def test_read_main():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "Hello world!"}


def test_hello_name():
    name = "Arek"
    response = client.get(f"/hello/{name}")
    assert response.status_code == 200
    assert response.text == f'"Hello {name}"'


def test_counter():
    response = client.get(f"/counter")
    assert response.status_code == 200
    assert response.text == "1"
    # 2nd try
    response = client.get(f"/counter")
    assert response.status_code == 200
    assert response.text == "2"


def test_root():
    response = client.get("/")
    assert response.status_code == 200
    assert response.text == '{"message":"Hello world!"}'


def test_method():
    response = client.get("/method")
    assert response.status_code == 200
    assert response.text == '{"method":"GET"}'


def test_auth():
    password = "haslo"
    password_hash = "013c6889f799cd986a735118e1888727d1435f7f623d05d58c61bf2cd8b49ac90105e5786ceaabd62bbc27336153d0d316b2d13b36804080c44aa6198c533215"
    response = client.get(f"/auth?password={password}&password_hash={password_hash}")
    assert response.status_code == 204

    password_hash = "f34ad4b3ae1e2cf33092e2abb60dc0444781c15d0e2e9ecdb37e4b14176a0164027b05900e09fa0f61a1882e0b89fbfa5dcfcc9765dd2ca4377e2c794837e091"
    response = client.get(f"/auth?password={password}&password_hash={password_hash}")
    assert response.status_code == 401

    response = client.get("/auth")
    assert response.status_code == 401


def test_register():
    name = "Jan"
    surname = "Kowalski"
    today = datetime.today()
    register_date = today.isoformat()[0:10]
    add_days = 11
    vaccination_date = (today+timedelta(days=add_days)).isoformat()[0:10]
    # ASSERT
    response = client.post(f"/register", json={"name": name, "surname": surname})
    ass = {"id": 1, "name": name, "surname": surname, "register_date": register_date,
           "vaccination_date": vaccination_date}
    assert response.status_code == 201
    assert response.json() == ass


def test_patient():
    name = "Jan"
    surname = "Kowalski"
    today = datetime.today()
    register_date = today.isoformat()[0:10]
    patient_id = 1
    response = client.get(f"patient/{patient_id}")
    add_days = 11
    vaccination_date = (today + timedelta(days=add_days)).isoformat()[0:10]
    assert response.status_code == 200
    assert response.json() == {"id": 1, "name": name, "surname": surname, "register_date": register_date,
                               "vaccination_date": vaccination_date}


@app.on_event("startup")
async def startup():
    app.db_connection = sqlite3.connect("northwind.db")
    app.db_connection.text_factory = lambda b: b.decode(errors="ignore")  # northwind specific


@app.on_event("shutdown")
async def shutdown():
    app.db_connection.close()


def test_categories():
    with TestClient(app) as client:
        id = 12323
        name = "ABC"
        new_name = "FGH"
        response = client.put(f"categories/{id}", json={"name": name})
        assert response.status_code == 404
        response = client.delete(f"/categories/{id}")
        assert response.status_code == 404

        response = client.post("/categories", json={"name": name})
        assert response.status_code == 201
        assert response.json() == {"id": id, "name": name}
        response = client.put(f"/categories/{id}", json={"name": new_name})
        assert response.status_code == 200
        assert response.json() == {"id": id, "name": new_name}
        response = client.delete(f"/categories/{id}")
        assert response.status_code == 200
        assert response.json() == {"deleted": 1}