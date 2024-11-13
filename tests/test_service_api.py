from unittest.mock import patch


def test_get_services(client):
    """
    Test the GET /services endpoint.
    """
    response = client.get("/services")
    assert response.status_code == 200
    data = response.get_json()
    assert len(data) > 0
    # assert all(d['consolidation_conflict'] is False for d in data)


def test_update_lifecycle(client):
    """Test the /services/<service_id>/lifecycle endpoint"""

    service_id = 1
    data = {"lifecycle_status": "released"}
    response = client.put(f"/services/{service_id}/lifecycle", json=data)
    assert response.status_code == 200
    assert response.json["message"] == "Lifecycle updated successfully"


def test_query_by_name(client):
    """Test querying services by name"""
    response = client.get("/services/query", query_string={"name": "Test Service"})

    assert response.status_code == 200
    assert len(response.json) >= 1


def test_query_by_team(client):
    """Test querying services by team"""
    response = client.get("/services/query", query_string={"team": "Team A"})

    assert response.status_code == 200
    assert len(response.json) >= 1
    assert response.json[0]["owner_team"] == "Team A"


def test_query_by_status(client):
    """Test querying services by lifecycle status"""
    response = client.get("/services/query", query_string={"status": "development"})

    assert response.status_code == 200
    assert len(response.json) >= 1
    assert all(
        service["lifecycle_status"] == "development" for service in response.json
    )


def test_query_multiple_filters(client):
    """Test querying services by multiple filters"""
    response = client.get(
        "/services/query", query_string={"name": "Test Service", "team": "Team A"}
    )

    assert response.status_code == 200
    assert len(response.json) == 1
    assert "Test Service" in response.json[0]["service_name"]
    assert response.json[0]["owner_team"] == "Team A"


def test_query_no_results(client):
    """Test querying services that return no results"""
    response = client.get(
        "/services/query", query_string={"name": "Non-existent Service"}
    )

    assert response.status_code == 200
    assert len(response.json) == 0


def test_list_conflicts(client):
    """Test GET /services/conflicts endpoint"""
    response = client.get("/services/conflicts")
    assert response.status_code == 200
    data = response.get_json()
    assert len(data) >= 1
    assert all(d.get('consolidation_conflict') is True for d in data)


def test_resolve_conflict(client):
    """Test the /services/<service_id>/resolve_conflict endpoint"""
    service_id = 2  # 2 and 3 are conflicting services
    response = client.put(f"/services/{service_id}/resolve_conflict")
    assert response.status_code == 200
    assert response.json["message"] == "Conflict resolved successfully"


def test_trigger_dag(client):
    """Test the /trigger/dag endpoint with mocked Airflow API response"""

    with patch("service_api.app.requests.post") as mock_airflow_post:
        mock_airflow_post.return_value.status_code = 200
        mock_airflow_post.return_value.text = "OK"

        data = {"repository_name": "repoA"}
        response = client.post("/trigger/dag", json=data)

        assert response.status_code == 200
        assert response.json["status"] == "Airflow DAG triggered successfully"
