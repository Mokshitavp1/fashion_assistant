import cv2
import numpy as np

# Test if we can read one of our existing images
test_files = ['test_clothing.jpg', 'test_item_0.jpg', 'test.jpg']

for filename in test_files:
    try:
        with open(filename, 'rb') as f:
            image_bytes = f.read()
            np_array = np.frombuffer(image_bytes, np.uint8)
            image = cv2.imdecode(np_array, cv2.IMREAD_COLOR)
            
            if image is not None:
                print(f"✅ {filename}: Valid - Shape: {image.shape}")
            else:
                print(f"❌ {filename}: Invalid - decode failed")
    except FileNotFoundError:
        print(f"⚠️  {filename}: Not found")
    except Exception as e:
        print(f"❌ {filename}: Error - {e}")