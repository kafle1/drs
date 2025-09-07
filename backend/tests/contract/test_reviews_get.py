import pytest
from fastapi.testclient import TestClient

@pytest.mark.asyncio
async def test_get_review_contract():
    # Test contract for GET /reviews/{reviewId}
    from backend.src.main import app  # Will fail

    client = TestClient(app)

    review_id = "test-review-id"

    # Test successful review retrieval
    response = client.get(f"/reviews/{review_id}")
    assert response.status_code == 200
    data = response.json()
    assert "id" in data
    assert "video_id" in data
    assert "decisions" in data
    assert isinstance(data["decisions"], list)

    # Test review not found
    response = client.get("/reviews/nonexistent-id")
    assert response.status_code == 404

    # Test invalid review id
    response = client.get("/reviews/invalid-id")
    assert response.status_code == 404
