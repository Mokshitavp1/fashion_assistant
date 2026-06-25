"""Temporary feature flow test - delete after use."""
import uuid
import requests
from io import BytesIO
from PIL import Image, ImageDraw

API = "http://127.0.0.1:8000"
email = f"feat.{uuid.uuid4().hex[:8]}@gmail.com"
password = "FeatTest123"
name = "Feature User"

r = requests.post(f"{API}/auth/register", json={"name": name, "email": email, "password": password})
l = requests.post(f"{API}/auth/login", data={"email": email, "password": password})
data = l.json()
access, uid = data["access_token"], data["user_id"]
H = {"Authorization": f"Bearer {access}"}

img = Image.new("RGB", (400, 600), (220, 200, 180))
draw = ImageDraw.Draw(img)
draw.ellipse([140, 80, 260, 200], fill=(210, 170, 140))
buf = BytesIO()
img.save(buf, format="JPEG")
buf.seek(0)

a = requests.post(
    f"{API}/users/{uid}/analyze",
    headers=H,
    files={"image": ("body.jpg", buf, "image/jpeg")},
    data={"height": "170", "weight": "65"},
)
print("analyze", a.status_code, a.json())

g = requests.get(f"{API}/users/{uid}", headers=H)
user = g.json()
print("profile", {k: user.get(k) for k in ["body_shape", "undertone", "height", "weight", "bmi"]})

for (r, g, b), cat in [((50, 100, 200), "top"), ((80, 80, 80), "bottom")]:
    shirt = Image.new("RGB", (200, 200), (r, g, b))
    sb = BytesIO()
    shirt.save(sb, format="JPEG")
    sb.seek(0)
    w = requests.post(
        f"{API}/users/{uid}/wardrobe/add",
        headers=H,
        files={"image": (f"{cat}.jpg", sb, "image/jpeg")},
        data={"category": cat, "season": "all"},
    )
    print("wardrobe add", cat, w.status_code)

wl = requests.get(f"{API}/users/{uid}/wardrobe", headers=H)
print("wardrobe list", wl.status_code, wl.json().get("total_items"))

o = requests.get(f"{API}/users/{uid}/outfits/recommend?limit=3", headers=H)
print("outfits", o.status_code, len(o.json().get("recommended_outfits", [])))

d = requests.get(f"{API}/users/{uid}/wardrobe/discard-recommendations", headers=H)
print("discard", d.status_code, len(d.json().get("recommendations", [])))

shop = Image.new("RGB", (200, 200), (200, 50, 50))
shb = BytesIO()
shop.save(shb, format="JPEG")
shb.seek(0)
s = requests.post(
    f"{API}/users/{uid}/shopping/analyze",
    headers=H,
    files={"image": ("shop.jpg", shb, "image/jpeg")},
)
print("shopping", s.status_code, list(s.json().keys()))

lo = requests.post(f"{API}/auth/logout", json={"refresh_token": data["refresh_token"]})
print("logout", lo.status_code)
l2 = requests.post(f"{API}/auth/login", data={"email": email, "password": password})
print("relogin", l2.status_code)
wl2 = requests.get(
    f"{API}/users/{uid}/wardrobe",
    headers={"Authorization": f"Bearer {l2.json()['access_token']}"},
)
print("wardrobe after relogin", wl2.status_code, wl2.json().get("total_items"))
