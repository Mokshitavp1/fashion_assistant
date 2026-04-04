import requests

BASE_URL = "http://127.0.0.1:8000"
EMAIL = "test_wardrobe@example.com"
PASSWORD = "TestWardrobePass123"


def get_auth_headers():
    register_resp = requests.post(
        f"{BASE_URL}/auth/register",
        json={"name": "Wardrobe User", "email": EMAIL, "password": PASSWORD},
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


user_id, headers = get_auth_headers()

# Download a test clothing image
print("=== Downloading Test Image ===")
img_url = "https://images.unsplash.com/photo-1521572163474-6864f9cf17ab?w=400"  # T-shirt image
img_response = requests.get(img_url)
with open('test_clothing.jpg', 'wb') as f:
    f.write(img_response.content)
print("✅ Test image downloaded")

# Test 1: Add clothing item
print("\n=== Adding Clothing Item ===")
with open('test_clothing.jpg', 'rb') as f:
    response = requests.post(
        f"{BASE_URL}/users/{user_id}/wardrobe/add",
        headers=headers,
        files={'image': f},
        data={
            'category': 'top',
            'season': 'summer'
        }
    )
    print(f"Status Code: {response.status_code}")
    print(f"Response Text: {response.text}")  # Show raw response
    
    if response.status_code == 200:
        print("✅ Item added!")
        result = response.json()
        print(f"   Type: {result['item']['type']}")
        print(f"   Color: {result['item']['color_primary']}")
        print(f"   Pattern: {result['item']['pattern']}")
    else:
        print(f"❌ Error occurred")

# Test 2: Get wardrobe
print("\n=== Getting Wardrobe ===")
response = requests.get(f"{BASE_URL}/users/{user_id}/wardrobe", headers=headers)
if response.status_code == 200:
    result = response.json()
    print(f"✅ Total items: {result['total_items']}")
    for item in result['items']:
        print(f"  - {item['category']}: {item['color_primary']} {item['type']} ({item['pattern']})")
else:
    print(f"❌ Error: {response.text}")