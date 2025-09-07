import pytest
from fastapi.testclient import TestClient

@pytest.mark.asyncio
async def test_get_trajectory_contract():
    # Test contract for GET /videos/{videoId}/trajectory
    from backend.src.main import app  # Will fail

    client = TestClient(app)

    video_id = "test-video-id"

    # Test successful trajectory retrieval
    response = client.get(f"/videos/{video_id}/trajectory")
    assert response.status_code == 200
    data = response.json()
    assert "video_id" in data
    assert "points" in data
    assert "confidence_score" in data
    assert isinstance(data["points"], list)

    # Test trajectory not available
    response = client.get("/videos/no-trajectory-id/trajectory")
    assert response.status_code == 404

    # Test invalid video id
    response = client.get("/videos/invalid-id/trajectory")
    assert response.status_code == 404
