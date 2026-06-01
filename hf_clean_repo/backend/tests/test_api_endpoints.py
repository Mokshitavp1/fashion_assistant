from __future__ import annotations

from backend import main as app_module
from io import BytesIO


def make_png_bytes(color: tuple[int, int, int] = (255, 0, 0)) -> bytes:
    from PIL import Image

    buffer = BytesIO()
    Image.new("RGB", (1, 1), color).save(buffer, format="PNG")
    return buffer.getvalue()


def _register_and_login(client, email: str, password: str):
    register_response = client.post(
        "/auth/register",
        json={"name": "API User", "email": email, "password": password},
    )
    assert register_response.status_code == 200
    verification_token = register_response.json()["verification_token"]

    verify_response = client.post(
        "/auth/verify-email",
        json={"verification_token": verification_token},
    )
    assert verify_response.status_code == 200

    login_response = client.post(
        "/auth/login",
        data={"email": email, "password": password},
    )
    assert login_response.status_code == 200
    payload = login_response.json()
    return payload["user_id"], payload["access_token"], payload["refresh_token"]


def test_profile_endpoint_requires_auth(client) -> None:
    response = client.get("/users/1")
    assert response.status_code == 401
    assert response.json()["detail"] == "Missing authorization token"


def test_authenticated_analyze_updates_profile_and_get_user_returns_saved_data(client, monkeypatch) -> None:
    email = "profile.api.user@gmail.com"
    password = "ProfileApi123"
    user_id, access_token, _ = _register_and_login(client, email, password)

    async def run_immediately(job_name, func, *args, **kwargs):
        return func(*args, **kwargs)

    def fake_skin_tone_analysis(image_array):
        return (123, 111, 99), "warm"

    def fake_body_shape_analysis(image_array, height, weight):
        return {
            "body_shape": "rectangle",
            "confidence": 0.91,
            "measurements": {"chest": 92, "waist": 78},
            "bmi": 22.5,
        }

    def fake_store_encrypted_image(**kwargs):
        return "image-123", "encrypted://image-123"

    monkeypatch.setattr(app_module, "run_bounded_image_job", run_immediately)
    monkeypatch.setattr(app_module, "_analyze_skin_tone", fake_skin_tone_analysis)
    monkeypatch.setattr(app_module, "classify_body_shape_with_bmi", fake_body_shape_analysis)
    monkeypatch.setattr(app_module, "store_encrypted_image", fake_store_encrypted_image)

    analyze_response = client.post(
        f"/users/{user_id}/analyze",
        headers={"Authorization": f"Bearer {access_token}"},
        files={"image": ("profile.png", make_png_bytes(), "image/png")},
        data={"height": "170", "weight": "65"},
    )
    assert analyze_response.status_code == 200
    analyze_payload = analyze_response.json()
    assert analyze_payload["user_id"] == user_id
    assert analyze_payload["body_shape"] == "rectangle"
    assert analyze_payload["undertone"] == "warm"

    profile_response = client.get(
        f"/users/{user_id}",
        headers={"Authorization": f"Bearer {access_token}"},
    )
    assert profile_response.status_code == 200
    profile_payload = profile_response.json()
    assert profile_payload["id"] == user_id
    assert profile_payload["email"] == email
    assert profile_payload["body_shape"] == "rectangle"
    assert profile_payload["undertone"] == "warm"
    assert profile_payload["profile_image_url"].endswith("/images/image-123")


def test_profile_endpoint_blocks_other_user_access(client) -> None:
    _, first_access_token, _ = _register_and_login(
        client,
        "first.api.user@gmail.com",
        "FirstApi123",
    )
    second_user_id, _, _ = _register_and_login(
        client,
        "second.api.user@gmail.com",
        "SecondApi123",
    )

    forbidden_response = client.get(
        f"/users/{second_user_id}",
        headers={"Authorization": f"Bearer {first_access_token}"},
    )
    assert forbidden_response.status_code == 403
    assert forbidden_response.json()["detail"] == "Access denied"