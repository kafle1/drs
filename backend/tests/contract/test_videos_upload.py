import pytest
from httpx import AsyncClient
from fastapi.testclient import TestClient

# This test will fail until the app is implemented
@pytest.mark.asyncio
async def test_upload_video_contract():
    # Test contract for POST /videos/upload
    # This should fail with import error until app is created
    from backend.src.main import app  # Will fail

    client = TestClient(app)

    # Test with valid video file
    with open("test_video.mp4", "rb") as f:
        response = client.post("/videos/upload", files={"file": ("test.mp4", f, "video/mp4")})

    assert response.status_code == 201
    assert "id" in response.json()
    assert "status" in response.json()

    # Test with invalid file type
    response = client.post("/videos/upload", files={"file": ("test.txt", b"invalid", "text/plain")})
    assert response.status_code == 400

    # Test without file
    response = client.post("/videos/upload")
    assert response.status_code == 422
