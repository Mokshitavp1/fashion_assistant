from __future__ import annotations

def _register_verified_user(client, email: str, password: str, name: str = "Auth User"):
    register_response = client.post(
        "/auth/register",
        json={"name": name, "email": email, "password": password},
    )
    assert register_response.status_code == 200
    register_payload = register_response.json()
    assert register_payload["email_verification_required"] is True
    assert register_payload["email"] == email
    assert register_payload["verification_token"]

    verify_response = client.post(
        "/auth/verify-email",
        json={"verification_token": register_payload["verification_token"]},
    )
    assert verify_response.status_code == 200
    assert verify_response.json()["email_verification_required"] is False


def _login(client, email: str, password: str):
    login_response = client.post(
        "/auth/login",
        data={"email": email, "password": password},
    )
    assert login_response.status_code == 200
    payload = login_response.json()
    assert payload["token_type"] == "bearer"
    assert payload["access_token"]
    assert payload["refresh_token"]
    return payload


def test_auth_flow_covers_registration_login_refresh_logout_and_reset(client) -> None:
    email = "auth.flow.user@gmail.com"
    password = "AuthFlow123"

    register_response = client.post(
        "/auth/register",
        json={"name": "Auth Flow", "email": email, "password": password},
    )
    assert register_response.status_code == 200
    verification_token = register_response.json()["verification_token"]

    unverified_login = client.post(
        "/auth/login",
        data={"email": email, "password": password},
    )
    assert unverified_login.status_code == 403
    assert unverified_login.json()["detail"] == "Please confirm your email before signing in"

    verify_response = client.post(
        "/auth/verify-email",
        json={"verification_token": verification_token},
    )
    assert verify_response.status_code == 200

    login_payload = _login(client, email, password)
    access_token = login_payload["access_token"]
    refresh_token = login_payload["refresh_token"]

    sessions_response = client.get(
        "/auth/sessions",
        headers={"Authorization": f"Bearer {access_token}"},
    )
    assert sessions_response.status_code == 200
    sessions_payload = sessions_response.json()
    assert sessions_payload["total_sessions"] == 1
    assert sessions_payload["active_sessions"] == 1

    refresh_response = client.post(
        "/auth/refresh",
        json={"refresh_token": refresh_token},
    )
    assert refresh_response.status_code == 200
    refreshed_payload = refresh_response.json()
    assert refreshed_payload["access_token"] != access_token
    assert refreshed_payload["refresh_token"] != refresh_token

    old_refresh_retry = client.post(
        "/auth/refresh",
        json={"refresh_token": refresh_token},
    )
    assert old_refresh_retry.status_code == 401
    assert old_refresh_retry.json()["detail"] == "Refresh token already used"

    logout_response = client.post(
        "/auth/logout",
        json={"refresh_token": refreshed_payload["refresh_token"]},
    )
    assert logout_response.status_code == 200
    assert logout_response.json()["detail"] == "Logged out"

    sessions_after_logout = client.get(
        "/auth/sessions",
        headers={"Authorization": f"Bearer {refreshed_payload['access_token']}"},
    )
    assert sessions_after_logout.status_code == 200
    assert sessions_after_logout.json()["active_sessions"] == 0

    reset_request = client.post(
        "/auth/password-reset/request",
        json={"email": email},
    )
    assert reset_request.status_code == 200
    reset_token = reset_request.json()["reset_token"]

    confirm_response = client.post(
        "/auth/password-reset/confirm",
        json={"reset_token": reset_token, "new_password": "NewAuthFlow123"},
    )
    assert confirm_response.status_code == 200
    assert confirm_response.json()["detail"] == "Password reset successful"

    relogin = client.post(
        "/auth/login",
        data={"email": email, "password": "NewAuthFlow123"},
    )
    assert relogin.status_code == 200


def test_logout_all_revokes_every_session(client) -> None:
    email = "logout.all.user@gmail.com"
    password = "LogoutAll123"

    _register_verified_user(client, email, password)

    first_login = _login(client, email, password)
    second_login = _login(client, email, password)

    sessions_response = client.get(
        "/auth/sessions",
        headers={"Authorization": f"Bearer {second_login['access_token']}"},
    )
    assert sessions_response.status_code == 200
    assert sessions_response.json()["active_sessions"] == 2

    logout_all_response = client.post(
        "/auth/logout-all",
        headers={"Authorization": f"Bearer {second_login['access_token']}"},
    )
    assert logout_all_response.status_code == 200
    assert logout_all_response.json()["revoked_sessions"] == 2

    sessions_after_logout_all = client.get(
        "/auth/sessions",
        headers={"Authorization": f"Bearer {first_login['access_token']}"},
    )
    assert sessions_after_logout_all.status_code == 200
    assert sessions_after_logout_all.json()["active_sessions"] == 0