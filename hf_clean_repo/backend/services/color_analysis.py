# write a function detect_face_region that:
# - accepts an OpenCV BGR image
# - converts it to grayscale
# - uses OpenCV Haar Cascade to detect a face
# - selects the largest detected face
# - returns the cropped face region
# - raises a clear error if no face is detected
# write a function extract_dominant_skin_color that:
# - accepts a cropped face image
# - reshapes pixels for clustering
# - applies k-means to find dominant color
# - returns the dominant color as an (R, G, B) tuple
import cv2
from fastapi import HTTPException
import numpy as np
from sklearn.cluster import KMeans
def detect_face_region(image: cv2.Mat) -> cv2.Mat:
    gray_image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
    faces = face_cascade.detectMultiScale(gray_image, scaleFactor=1.1, minNeighbors=5)

    if len(faces) == 0:
        raise HTTPException(status_code=400, detail="No face detected in the image")

    # Select the largest detected face
    largest_face = max(faces, key=lambda rect: rect[2] * rect[3])
    x, y, w, h = largest_face
    face_region = image[y:y+h, x:x+w]
    return face_region

def extract_dominant_skin_color(face_image: cv2.Mat) -> tuple:
    pixels = face_image.reshape((-1, 3))
    kmeans = KMeans(n_clusters=3, n_init=10)
    kmeans.fit(pixels)
    dominant_color = kmeans.cluster_centers_[np.argmax(np.bincount(kmeans.labels_))]
    return tuple(map(int, dominant_color))
# write a function classify_undertone that:
# - accepts an (R, G, B) skin color tuple
# - classifies undertone as "warm", "cool", or "neutral"
# - uses simple RGB comparison rules
# - returns the undertone as a string
def classify_undertone(skin_color: tuple) -> str:
    r, g, b = skin_color
    if r > g and r > b:
        return "warm"
    elif b > r and b > g:
        return "cool"
    else:
        return "neutral"
def classify_skin_undertone(face_image: cv2.Mat) -> str: 
    skin_color = extract_dominant_skin_color(face_image)
    undertone = classify_undertone(skin_color)
    return undertone   