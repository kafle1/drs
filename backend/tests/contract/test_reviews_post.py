import pytest
from fastapi.testclient import TestClient

@pytest.mark.asyncio
async def test_create_review_contract():
    # Test contract for POST /reviews
    from backend.src.main import app  # Will fail

    client = TestClient(app)

    # Test successful review creation
    review_data = {
        "video_id": "test-video-id",
        "decisions": [
            {
                "type": "lbw",
                "outcome": "out",
                "timestamp": 10.5,
                "confidence": 0.85
            }
        ],
        "notes": "Test review"
    }
    response = client.post("/reviews", json=review_data)
    assert response.status_code == 201
    assert "id" in response.json()
    assert "video_id" in response.json()

    # Test with invalid data
    invalid_data = {"video_id": "test"}
    response = client.post("/reviews", json=invalid_data)
    assert response.status_code == 422

    # Test without required fields
    response = client.post("/reviews", json={})
    assert response.status_code == 422
