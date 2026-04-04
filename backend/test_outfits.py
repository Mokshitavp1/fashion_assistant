import requests

BASE_URL = "http://127.0.0.1:8000"
EMAIL = "test_outfits@example.com"
PASSWORD = "TestOutfitsPass123"


def get_auth_headers():
    register_resp = requests.post(
        f"{BASE_URL}/auth/register",
        json={"name": "Outfits User", "email": EMAIL, "password": PASSWORD},
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

# Step 1: Create user
print("=== Creating User ===")
user_id, headers = get_auth_headers()
print(f"✅ Using user ID: {user_id}")

# Step 2: Analyze user (required for outfit recommendations)
print("\n=== Analyzing User ===")
# Download a test profile image
img_url = "https://images.unsplash.com/photo-1494790108377-be9c29b29330?w=400"
img_response = requests.get(img_url)
with open('profile.jpg', 'wb') as f:
    f.write(img_response.content)

with open('profile.jpg', 'rb') as f:
    response = requests.post(
        f"{BASE_URL}/users/{user_id}/analyze",
        headers=headers,
        files={'image': f},
        data={'height': 170, 'weight': 65}
    )
    if response.status_code == 200:
        print(f"✅ User analyzed: {response.json()['body_shape']}, {response.json()['undertone']}")
    else:
        print(f"❌ Analysis failed: {response.text}")

# Step 3: Add wardrobe items
print("\n=== Adding More Wardrobe Items ===")

# Download test images
test_items = [
    ("https://images.unsplash.com/photo-1521572163474-6864f9cf17ab?w=400", "top", "summer"),
    ("https://images.unsplash.com/photo-1542272604-787c3835535d?w=400", "bottom", "all"),
    ("https://images.unsplash.com/photo-1551028719-00167b16eac5?w=400", "top", "winter"),
]

for idx, (url, category, season) in enumerate(test_items):
    img_response = requests.get(url)
    filename = f'test_item_{idx}.jpg'
    with open(filename, 'wb') as f:
        f.write(img_response.content)
    
    with open(filename, 'rb') as f:
        response = requests.post(
            f"{BASE_URL}/users/{user_id}/wardrobe/add",
            headers=headers,
            files={'image': f},
            data={'category': category, 'season': season}
        )
        if response.status_code == 200:
            print(f"✅ Added {category} for {season}")

# Test outfit recommendations
print("\n=== Getting Outfit Recommendations ===")
response = requests.get(
    f"{BASE_URL}/users/{user_id}/outfits/recommend?limit=5",
    headers=headers,
)

if response.status_code == 200:
    result = response.json()
    print(f"\n✅ Generated {result['total_recommendations']} outfit recommendations!")
    print(f"Body Shape: {result['body_shape']}")
    print(f"Undertone: {result['undertone']}")
    print(f"Total Wardrobe Items: {result['total_wardrobe_items']}")
    
    for outfit in result['recommended_outfits']:
        print(f"\n--- Outfit #{outfit['outfit_number']} ---")
        print(f"Overall Score: {outfit['overall_score']}")
        print(f"Color Harmony: {outfit['color_harmony_score']}")
        print(f"Body Shape Fit: {outfit['body_shape_score']}")
        print(f"Items:")
        for item in outfit['items']:
            print(f"  - {item['color']} {item['type']} ({item['category']})")
else:
    print(f"❌ Error: {response.text}")