import pytest

@pytest.fixture
def create_users_for_tickets(client):
    """Create common users for ticket tests."""
    emp_resp = client.post("/users/", json={
        "username": "ticket_emp",
        "email": "ticket_emp@example.com",
        "role": "employee"
    })
    assert emp_resp.status_code == 201, emp_resp.json()
    emp = emp_resp.json()

    agent_resp = client.post("/users/", json={
        "username": "ticket_agent",
        "email": "ticket_agent@example.com",
        "role": "agent",
        "department": "IT"
    })
    assert agent_resp.status_code == 201, agent_resp.json()
    agent = agent_resp.json()

    triage_resp = client.post("/users/", json={
        "username": "ticket_triage",
        "email": "ticket_triage@example.com",
        "role": "triage_officer"
    })
    assert triage_resp.status_code == 201, triage_resp.json()
    triage = triage_resp.json()

    return {"employee": emp, "agent": agent, "triage": triage}


def test_create_ticket_success(client, create_users_for_tickets):
    emp_id = create_users_for_tickets["employee"]["id"]
    payload = {"subject": "Test Ticket", "description": "This is a test ticket"}
    response = client.post("/tickets/", json=payload, headers={"X-User-ID": str(emp_id)})
    assert response.status_code == 201, response.json()
    data = response.json()
    assert data["subject"] == "Test Ticket"
    assert "id" in data


def test_create_ticket_forbidden_for_agent(client, create_users_for_tickets):
    agent_id = create_users_for_tickets["agent"]["id"]
    payload = {"subject": "Agent Ticket", "description": "Agents cannot create tickets"}
    response = client.post("/tickets/", json=payload, headers={"X-User-ID": str(agent_id)})
    assert response.status_code == 403
    assert "Only employees" in response.json()["detail"]


def test_get_my_tickets(client, create_users_for_tickets):
    emp_id = create_users_for_tickets["employee"]["id"]
    # Create a ticket
    resp_create = client.post("/tickets/", json={
        "subject": "My Ticket",
        "description": "Test"
    }, headers={"X-User-ID": str(emp_id)})
    assert resp_create.status_code == 201, resp_create.json()

    response = client.get("/tickets/my", headers={"X-User-ID": str(emp_id)})
    assert response.status_code == 200, response.json()
    assert any(t["subject"] == "My Ticket" for t in response.json())


def test_triage_ticket_flow(client, create_users_for_tickets):
    emp_id = create_users_for_tickets["employee"]["id"]
    triage_id = create_users_for_tickets["triage"]["id"]
    agent_id = create_users_for_tickets["agent"]["id"]

    # Create ticket by employee
    resp_ticket = client.post("/tickets/", json={
        "subject": "Needs triage",
        "description": "Triaging..."
    }, headers={"X-User-ID": str(emp_id)})
    assert resp_ticket.status_code == 201, resp_ticket.json()
    ticket_id = resp_ticket.json()["id"]

    # Triage officer triages it
    update_data = {
        "priority": "high",
        "assigned_team": "IT",
        "assignee_id": agent_id
    }
    resp_triage = client.put(
        f"/tickets/{ticket_id}/triage",
        json=update_data,
        headers={"X-User-ID": str(triage_id)}
    )
    assert resp_triage.status_code == 200, resp_triage.json()
    assert resp_triage.json()["status"] == "triaged"


def test_resolve_ticket_not_in_progress(client, create_users_for_tickets):
    agent_id = create_users_for_tickets["agent"]["id"]
    emp_id = create_users_for_tickets["employee"]["id"]

    # Create ticket
    resp_ticket = client.post("/tickets/", json={
        "subject": "Resolve fail",
        "description": "Should fail"
    }, headers={"X-User-ID": str(emp_id)})
    assert resp_ticket.status_code == 201, resp_ticket.json()
    ticket_id = resp_ticket.json()["id"]

    # Try resolve (status = new) → should fail
    resp_resolve = client.put(
        f"/tickets/{ticket_id}/resolve",
        json={"resolution_notes": "done"},
        headers={"X-User-ID": str(agent_id)}
    )
    assert resp_resolve.status_code == 400
    assert "in progress" in resp_resolve.json()["detail"]