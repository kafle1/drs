import pytest
from fastapi.testclient import TestClient

@pytest.mark.asyncio
async def test_review_creation_workflow():
    # Integration test for review creation workflow
    from backend.src.main import app  # Will fail

    client = TestClient(app)

    video_id = "existing-video-id"

    # Create review
    review_data = {
        "video_id": video_id,
        "decisions": [
            {
                "type": "run_out",
                "outcome": "out",
                "timestamp": 15.2,
                "confidence": 0.95
            },
            {
                "type": "caught",
                "outcome": "out",
                "timestamp": 20.1,
                "confidence": 0.88
            }
        ],
        "notes": "Comprehensive review of key moments"
    }

    response = client.post("/reviews", json=review_data)
    assert response.status_code == 201
    review = response.json()
    assert review["video_id"] == video_id
    assert len(review["decisions"]) == 2

    # Retrieve and verify
    get_response = client.get(f"/reviews/{review['id']}")
    assert get_response.status_code == 200
    retrieved_review = get_response.json()
    assert retrieved_review["decisions"] == review_data["decisions"]
    assert retrieved_review["notes"] == review_data["notes"]
