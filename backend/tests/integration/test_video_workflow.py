import pytest
from fastapi.testclient import TestClient

@pytest.mark.asyncio
async def test_video_upload_and_tracking_workflow():
    # Integration test for video upload and tracking workflow
    from backend.src.main import app  # Will fail

    client = TestClient(app)

    # Step 1: Upload video
    with open("test_video.mp4", "rb") as f:
        upload_response = client.post("/videos/upload", files={"file": ("test.mp4", f, "video/mp4")})
    assert upload_response.status_code == 201
    video_id = upload_response.json()["id"]

    # Step 2: Start tracking
    track_response = client.post(f"/videos/{video_id}/track")
    assert track_response.status_code == 202

    # Step 3: Get trajectory (assuming processing is fast for test)
    trajectory_response = client.get(f"/videos/{video_id}/trajectory")
    assert trajectory_response.status_code == 200
    trajectory_data = trajectory_response.json()
    assert trajectory_data["video_id"] == video_id
    assert "points" in trajectory_data

    # Step 4: Create review
    review_data = {
        "video_id": video_id,
        "decisions": [
            {
                "type": "lbw",
                "outcome": "out",
                "timestamp": 5.0,
                "confidence": 0.9
            }
        ]
    }
    review_response = client.post("/reviews", json=review_data)
    assert review_response.status_code == 201
    review_id = review_response.json()["id"]

    # Step 5: Get review
    get_review_response = client.get(f"/reviews/{review_id}")
    assert get_review_response.status_code == 200
    assert get_review_response.json()["video_id"] == video_id
