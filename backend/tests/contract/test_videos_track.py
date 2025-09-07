import pytest
from fastapi.testclient import TestClient

@pytest.mark.asyncio
async def test_track_video_contract():
    # Test contract for POST /videos/{videoId}/track
    from backend.src.main import app  # Will fail

    client = TestClient(app)

    video_id = "test-video-id"

    # Test successful tracking start
    response = client.post(f"/videos/{video_id}/track")
    assert response.status_code == 202
    assert "status" in response.json()
    assert response.json()["status"] == "processing"

    # Test with invalid video id
    response = client.post("/videos/invalid-id/track")
    assert response.status_code == 404

    # Test tracking already in progress
    # Second call should return 409
    response = client.post(f"/videos/{video_id}/track")
    assert response.status_code == 409
