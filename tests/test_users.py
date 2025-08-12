import pytest
 
# ---- USER TESTS ----
def test_create_user_success(client):
    payload = {
        "username": "employee1",
        "email": "emp1@example.com",
        "role": "employee"
    }
    response = client.post("/users/", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["username"] == "employee1"
    assert data["role"] == "employee"
    assert "id" in data


def test_create_duplicate_user(client):
    # Create once
    payload = {
        "username": "dupuser",
        "email": "dup@example.com",
        "role": "employee"
    }
    client.post("/users/", json=payload)

    # Try again → should fail
    response = client.post("/users/", json=payload)
    assert response.status_code == 400
    assert response.json()["detail"] == "Username or email already exists"


def test_create_agent_without_department(client):
    payload = {
        "username": "agent1",
        "email": "agent1@example.com",
        "role": "agent"
    }
    response = client.post("/users/", json=payload)
    assert response.status_code == 400
    assert "Agents must have a department" in response.json()["detail"]


def test_get_users_success(client):
    # Create a triage officer
    triage_payload = {
        "username": "triage1",
        "email": "triage1@example.com",
        "role": "triage_officer"
    }
    triage_id = client.post("/users/", json=triage_payload).json()["id"]

    # Create a normal employee (to list)
    emp_payload = {
        "username": "emp2",
        "email": "emp2@example.com",
        "role": "employee"
    }
    client.post("/users/", json=emp_payload)

    # Fetch users using triage officer's ID
    response = client.get("/users/", headers={"X-User-ID": str(triage_id)})
    assert response.status_code == 200
    assert any(user["username"] == "emp2" for user in response.json())


def test_get_users_forbidden_for_employee(client):
    emp_payload = {
        "username": "emp3",
        "email": "emp3@example.com",
        "role": "employee"
    }
    emp_id = client.post("/users/", json=emp_payload).json()["id"]

    response = client.get("/users/", headers={"X-User-ID": str(emp_id)})
    assert response.status_code == 403


def test_get_user_self_and_forbidden_other(client):
    emp_payload = {
        "username": "emp4",
        "email": "emp4@example.com",
        "role": "employee"
    }
    emp_id = client.post("/users/", json=emp_payload).json()["id"]

    # Can fetch self
    resp_self = client.get(f"/users/{emp_id}", headers={"X-User-ID": str(emp_id)})
    assert resp_self.status_code == 200

    # Create another employee
    emp_payload2 = {
        "username": "emp5",
        "email": "emp5@example.com",
        "role": "employee"
    }
    emp2_id = client.post("/users/", json=emp_payload2).json()["id"]

    # emp1 trying to fetch emp2 → forbidden
    resp_other = client.get(f"/users/{emp2_id}", headers={"X-User-ID": str(emp_id)})
    assert resp_other.status_code == 403