import requests

BASE_URL = "http://127.0.0.1:8000"
EMAIL = "test_with_database@example.com"
PASSWORD = "TestDbPass123"

# Test 1: Login or create a user
print("=== Logging In / Creating User ===")
login_response = requests.post(
    f"{BASE_URL}/auth/login",
    data={"email": EMAIL, "password": PASSWORD},
)

if login_response.status_code == 200:
    payload = login_response.json()
    user_id = payload["user_id"]
    token = payload["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    print(f"✅ Logged in as user ID: {user_id}")
else:
    response = requests.post(
        f"{BASE_URL}/auth/register",
        json={
            "name": "Test User",
            "email": EMAIL,
            "password": PASSWORD,
        }
    )
    if response.status_code != 200:
        print(f"Error: {response.text}")
        exit()
    payload = response.json()
    user_id = payload["user_id"]
    token = payload["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    print(f"✅ User created with ID: {user_id}")

# Test 2: Analyze the user
print("\n=== Analyzing User ===")
try:
    face_urls = [
        "https://images.unsplash.com/photo-1544005313-94ddf0286df2?w=400",
        "https://images.unsplash.com/photo-1494790108377-be9c29b29330?w=400",
    ]
    analyzed = False
    for idx, img_url in enumerate(face_urls):
        img_resp = requests.get(img_url, timeout=30)
        filename = f"test_profile_{idx}.jpg"
        with open(filename, "wb") as f:
            f.write(img_resp.content)

        with open(filename, 'rb') as f:
            response = requests.post(
                f"{BASE_URL}/users/{user_id}/analyze",
                headers=headers,
                files={'image': f},
                data={'height': 170, 'weight': 65}
            )

        if response.status_code == 200:
            print("✅ Analysis successful!")
            result = response.json()
            print(f"   Body Shape: {result['body_shape']}")
            print(f"   Undertone: {result['undertone']}")
            print(f"   BMI: {result['bmi']}")
            print(f"   Confidence: {result['body_shape_confidence']}")
            analyzed = True
            break

    if not analyzed:
        print(f"❌ Error: {response.json()}")
except FileNotFoundError:
    print("❌ test.jpg not found. Please add a test image.")
    exit()

# Test 3: Get user profile
print("\n=== Getting User Profile ===")
response = requests.get(f"{BASE_URL}/users/{user_id}", headers=headers)
if response.status_code == 200:
    print("✅ User profile retrieved!")
    user = response.json()
    print(f"   Name: {user['name']}")
    print(f"   Email: {user['email']}")
    print(f"   Body Shape: {user['body_shape']}")
    print(f"   Undertone: {user['undertone']}")
    print(f"   BMI: {user['bmi']}")
else:
    print(f"❌ Error: {response.json()}")