from fastapi.testclient import TestClient

from aether.api.app import create_app


class TestAPI:
    def test_health(self):
        app = create_app()
        client = TestClient(app)
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json()["status"] == "ok"

    def test_create_task(self):
        app = create_app()
        client = TestClient(app)
        response = client.post("/task", json={"task": "open calculator"})
        assert response.status_code == 202
        assert "task_id" in response.json()

    def test_get_task(self):
        app = create_app()
        client = TestClient(app)
        create_resp = client.post("/task", json={"task": "test"})
        task_id = create_resp.json()["task_id"]
        get_resp = client.get(f"/task/{task_id}")
        assert get_resp.status_code == 200
        assert get_resp.json()["task_id"] == task_id
