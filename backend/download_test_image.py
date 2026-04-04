import requests

url = "https://images.unsplash.com/photo-1539571696357-5a69c17a67c6?w=400"
response = requests.get(url)

with open('test.jpg', 'wb') as f:
    f.write(response.content)

print("Test image downloaded as test.jpg")