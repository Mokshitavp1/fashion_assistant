import requests

BASE_URL = "http://127.0.0.1:8000"
EMAIL = "test_api@example.com"
PASSWORD = "TestApiPass123"


def get_auth_headers():
    register_resp = requests.post(
        f"{BASE_URL}/auth/register",
        json={"name": "Test API User", "email": EMAIL, "password": PASSWORD},
    )

    if register_resp.status_code == 200:
        payload = register_resp.json()
    else:
        login_resp = requests.post(
            f"{BASE_URL}/auth/login",
            data={"email": EMAIL, "password": PASSWORD},
        )
        login_resp.raise_for_status()
        payload = login_resp.json()

    token = payload["access_token"]
    user_id = payload["user_id"]
    return user_id, {"Authorization": f"Bearer {token}"}


print("Testing server...")
response = requests.get(f"{BASE_URL}/")
print("Server status:", response.json())

print("\nTesting authenticated profile fetch...")
try:
    user_id, headers = get_auth_headers()
    profile_resp = requests.get(f"{BASE_URL}/users/{user_id}", headers=headers)
    print(f"Status: {profile_resp.status_code}")
    print(profile_resp.text)
except Exception as e:
    print(f"Error: {e}")