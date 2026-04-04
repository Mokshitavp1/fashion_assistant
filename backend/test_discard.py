import requests

BASE_URL = "http://127.0.0.1:8000"
EMAIL = "test_discard@example.com"
PASSWORD = "TestDiscardPass123"


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
            json={"name": "Discard User", "email": EMAIL, "password": PASSWORD},
        )
        register_resp.raise_for_status()
        payload = register_resp.json()

    token = payload["access_token"]
    user_id = payload["user_id"]
    return user_id, {"Authorization": f"Bearer {token}"}


def prepare_user_data(user_id, headers):
    # Analyze user profile
    profile_url = "https://images.unsplash.com/photo-1494790108377-be9c29b29330?w=400"
    profile_resp = requests.get(profile_url, timeout=30)
    with open("profile_discard.jpg", "wb") as f:
        f.write(profile_resp.content)

    with open("profile_discard.jpg", "rb") as f:
        requests.post(
            f"{BASE_URL}/users/{user_id}/analyze",
            headers=headers,
            files={"image": f},
            data={"height": 170, "weight": 65},
            timeout=90,
        )

    # Ensure at least one wardrobe item exists
    cloth_url = "https://images.unsplash.com/photo-1521572163474-6864f9cf17ab?w=400"
    cloth_resp = requests.get(cloth_url, timeout=30)
    with open("discard_item.jpg", "wb") as f:
        f.write(cloth_resp.content)

    with open("discard_item.jpg", "rb") as f:
        requests.post(
            f"{BASE_URL}/users/{user_id}/wardrobe/add",
            headers=headers,
            files={"image": f},
            data={"category": "top", "season": "all"},
            timeout=90,
        )


user_id, headers = get_auth_headers()
prepare_user_data(user_id, headers)

print("=== Getting Discard Recommendations ===")
response = requests.get(
    f"{BASE_URL}/users/{user_id}/wardrobe/discard-recommendations",
    headers=headers,
)

if response.status_code == 200:
    result = response.json()
    analysis = result['analysis']
    
    print(f"\n📊 Wardrobe Analysis for User #{user_id}")
    print(f"Body Shape: {result['body_shape']}")
    print(f"Undertone: {result['undertone']}")
    print(f"\nTotal Items: {analysis['total_items']}")
    print(f"✅ Items to Keep: {analysis['keep_count']}")
    print(f"🗑️  Items to Discard: {analysis['discard_count']}")
    
    if analysis['items_to_discard']:
        print("\n" + "="*50)
        print("🗑️  ITEMS RECOMMENDED FOR DISCARD:")
        print("="*50)
        for item in analysis['items_to_discard']:
            print(f"\n❌ {item['item_color']} {item['item_type']} (ID: {item['item_id']})")
            print(f"   Category: {item['item_category']}")
            print(f"   Overall Score: {item['overall_score']}/1.0")
            print(f"   📊 Breakdown:")
            print(f"      - Undertone Match: {item['undertone_score']}")
            print(f"      - Body Shape Fit: {item['body_shape_score']}")
            print(f"      - Versatility: {item['versatility_score']} ({item['potential_outfits']} outfits)")
            print(f"   📝 Reasons:")
            for reason in item['reasons']:
                print(f"      • {reason}")
    
    if analysis['items_to_keep']:
        print("\n" + "="*50)
        print("✅ ITEMS TO KEEP:")
        print("="*50)
        for item in analysis['items_to_keep'][:5]:  # Show top 5
            print(f"\n✅ {item['item_color']} {item['item_type']} (ID: {item['item_id']})")
            print(f"   Overall Score: {item['overall_score']}/1.0")
            print(f"   Can create {item['potential_outfits']} outfit(s)")
else:
    print(f"❌ Error: {response.text}")