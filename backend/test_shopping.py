import requests
import cv2
import numpy as np

BASE_URL = "http://127.0.0.1:8000"
EMAIL = "test_shopping@example.com"
PASSWORD = "TestShoppingPass123"


def get_auth_headers():
    login_resp = requests.post(
        f"{BASE_URL}/auth/login",
        data={"email": EMAIL, "password": PASSWORD},
    )
    if login_resp.status_code == 200:
        payload = login_resp.json()
    else:
        register_resp = requests.post(
            f"{BASE_URL}/auth/register",
            json={"name": "Shopping User", "email": EMAIL, "password": PASSWORD},
        )
        register_resp.raise_for_status()
        payload = register_resp.json()

    token = payload["access_token"]
    user_id = payload["user_id"]
    return user_id, {"Authorization": f"Bearer {token}"}


def prepare_user_data(user_id, headers):
    profile_url = "https://images.unsplash.com/photo-1494790108377-be9c29b29330?w=400"
    profile_resp = requests.get(profile_url, timeout=30)
    with open("profile_shopping.jpg", "wb") as f:
        f.write(profile_resp.content)

    with open("profile_shopping.jpg", "rb") as f:
        requests.post(
            f"{BASE_URL}/users/{user_id}/analyze",
            headers=headers,
            files={"image": f},
            data={"height": 170, "weight": 65},
            timeout=90,
        )

    cloth_url = "https://images.unsplash.com/photo-1521572163474-6864f9cf17ab?w=400"
    cloth_resp = requests.get(cloth_url, timeout=30)
    with open("shopping_item_seed.jpg", "wb") as f:
        f.write(cloth_resp.content)

    with open("shopping_item_seed.jpg", "rb") as f:
        requests.post(
            f"{BASE_URL}/users/{user_id}/wardrobe/add",
            headers=headers,
            files={"image": f},
            data={"category": "top", "season": "all"},
            timeout=90,
        )


user_id, headers = get_auth_headers()
prepare_user_data(user_id, headers)

# Download a test shopping item image
print("=== Downloading Test Shopping Item ===")
shopping_url = "https://images.unsplash.com/photo-1542272604-787c3835535d?w=400"  # Different image
img_response = requests.get(shopping_url)
with open('test.jpg', 'wb') as f:
    f.write(img_response.content)

# Validate the image
img = cv2.imread('test.jpg')
if img is None:
    print("❌ Downloaded image is invalid. Trying alternative...")
    shopping_url = "https://images.unsplash.com/photo-1521572163474-6864f9cf17ab?w=400"
    img_response = requests.get(shopping_url)
    with open('test.jpg', 'wb') as f:
        f.write(img_response.content)
    img = cv2.imread('test.jpg')
    if img is None:
        print("❌ Could not download valid image")
        exit(1)

print(f"✅ Downloaded valid test item ({img.shape[1]}x{img.shape[0]})")

print("\n=== Analyzing Shopping Item (test.jpg) ===")
with open('test.jpg', 'rb') as f:
    response = requests.post(
        f"{BASE_URL}/users/{user_id}/shopping/analyze",
        headers=headers,
        files={'image': f}
    )

print(f"Response Status: {response.status_code}")

if response.status_code == 200:
    result = response.json()
    analysis = result['analysis']
    
    print(f"\n🛍️ Shopping Analysis")
    print("="*60)
    
    # Item details
    item = analysis['item_classification']
    print(f"\n📦 Item Details:")
    print(f"   Type: {item['type']}")
    print(f"   Category: {item['category']}")
    print(f"   Color: {item['color_primary']}")
    if item['color_secondary']:
        print(f"   Secondary Color: {item['color_secondary']}")
    print(f"   Pattern: {item['pattern']}")
    
    # Wardrobe compatibility
    compat = analysis['wardrobe_compatibility']
    print(f"\n👗 Wardrobe Compatibility:")
    print(f"   Score: {compat['score']}/1.0")
    print(f"   Matches {compat['matching_items_count']} item(s) in your wardrobe")
    
    if compat['matching_items']:
        print(f"   Top matches:")
        for match in compat['matching_items'][:3]:
            print(f"      • {match['item_color']} {match['item_type']} ({match['harmony_type']} harmony)")
    else:
        print(f"   ⚠️  No matching items found")
    
    # Duplicate check
    dup = analysis['duplicate_check']
    if dup['is_duplicate']:
        print(f"\n⚠️  Duplicate Alert:")
        print(f"   You already own similar item(s):")
        for similar in dup['similar_items']:
            print(f"      • {similar['item_color']} {similar['item_type']} (ID: {similar['item_id']})")
    else:
        print(f"\n✅ No duplicates - this would be a new addition")
    
    # Body shape
    body = analysis['body_shape_compatibility']
    print(f"\n👤 Body Shape Compatibility:")
    print(f"   Score: {body['score']}/1.0")
    print(f"   Your shape: {body['body_shape']}")
    
    # Recommendation
    print(f"\n{'='*60}")
    rec = analysis['recommendation'].upper()
    emoji = "🎉" if rec == "BUY" else "🤔" if rec == "MAYBE" else "❌"
    print(f"{emoji} RECOMMENDATION: {rec}")
    print(f"{'='*60}")
    print("\n📝 Reasons:")
    for reason in analysis['reasons']:
        print(f"   {reason}")
    
else:
    print(f"❌ Error: {response.status_code}")
    print(f"Response: {response.text}")