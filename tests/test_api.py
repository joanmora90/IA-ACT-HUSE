from fastapi.testclient import TestClient

from ai_act_validator.main import create_app


def project_payload():
    return {
        "metadata": {
            "project_name": "Chatbot de prueba",
            "description": "Asistente informativo",
            "organisation_type": "PUBLIC_BODY",
            "role": "DEPLOYER",
            "assessment_date": "2026-09-01",
        }
    }


def test_start_and_submit_answer(settings):
    client = TestClient(create_app(settings))
    response = client.post("/api/v1/assessments", json=project_payload())
    assert response.status_code == 201
    body = response.json()
    assessment_id = body["assessment"]["id"]
    assert body["next_question"]["id"] == "Q001"

    response = client.post(
        f"/api/v1/assessments/{assessment_id}/answers",
        json={"question_id": "Q001", "value": True},
    )
    assert response.status_code == 200
    assert response.json()["next_question"]["id"] == "Q002"


def test_rejects_out_of_order_answer(settings):
    client = TestClient(create_app(settings))
    assessment_id = client.post("/api/v1/assessments", json=project_payload()).json()["assessment"][
        "id"
    ]
    response = client.post(
        f"/api/v1/assessments/{assessment_id}/answers",
        json={"question_id": "Q002", "value": True},
    )
    assert response.status_code == 409


def test_stateless_evaluation(settings):
    client = TestClient(create_app(settings))
    payload = project_payload() | {
        "answers": {
            "Q001": True,
            "Q002": True,
            "Q003": "NONE",
            "Q004": ["NONE"],
            "Q006": False,
            "Q008": "NONE",
            "Q013": "DIRECT_NOT_OBVIOUS",
            "Q014": ["NONE"],
            "Q015": ["NONE"],
        }
    }
    response = client.post("/api/v1/evaluate", json=payload)
    assert response.status_code == 200
    assert response.json()["overall_status"] == "TRANSPARENCY_OBLIGATIONS"


def test_power_platform_next_question(settings):
    client = TestClient(create_app(settings))
    payload = {
        "project_name": "Prueba Power Apps",
        "organisation_type": "PUBLIC_BODY",
        "role": "DEPLOYER",
        "assessment_date": "2026-09-01",
        "answers": [
            {"question_id": "Q001", "value_json": "true"},
            {"question_id": "Q002", "value_json": "true"},
            {"question_id": "Q003", "value_json": '"NONE"'},
        ],
    }
    response = client.post("/api/v1/power-platform/next-question", json=payload)
    assert response.status_code == 200
    assert response.json()["next_question"]["id"] == "Q004"
