from fastapi.testclient import TestClient


def test_contact_allocation_respects_load_limit(client: TestClient) -> None:
    operator_payload = {"name": "Operator 1", "active": True, "load_limit": 1}
    response = client.post("/operators/", json=operator_payload)
    assert response.status_code == 201
    operator_id = response.json()["id"]

    source_payload = {
        "name": "Source A",
        "assignments": [
            {"operator_id": operator_id, "weight": 10},
        ],
    }
    response = client.post("/sources/", json=source_payload)
    assert response.status_code == 201
    source_id = response.json()["id"]

    contact_payload = {
        "lead_external_id": "lead-1",
        "lead_name": "Lead One",
        "source_id": source_id,
        "message": "First message",
    }
    response = client.post("/contacts/", json=contact_payload)
    assert response.status_code == 201
    assert response.json()["operator_id"] == operator_id

    second_contact_payload = {
        "lead_external_id": "lead-2",
        "lead_name": "Lead Two",
        "source_id": source_id,
    }
    response = client.post("/contacts/", json=second_contact_payload)
    assert response.status_code == 201
    assert response.json()["operator_id"] is None


def test_inactive_operator_is_skipped(client: TestClient) -> None:
    response = client.post("/operators/", json={"name": "Inactive", "active": False, "load_limit": 1})
    assert response.status_code == 201
    inactive_id = response.json()["id"]

    response = client.post("/operators/", json={"name": "Active", "active": True, "load_limit": 2})
    assert response.status_code == 201
    active_id = response.json()["id"]

    source_payload = {
        "name": "Source B",
        "assignments": [
            {"operator_id": inactive_id, "weight": 10},
            {"operator_id": active_id, "weight": 10},
        ],
    }
    response = client.post("/sources/", json=source_payload)
    assert response.status_code == 201
    source_id = response.json()["id"]

    contact_payload = {
        "lead_external_id": "lead-3",
        "source_id": source_id,
    }
    response = client.post("/contacts/", json=contact_payload)
    assert response.status_code == 201
    assert response.json()["operator_id"] == active_id


