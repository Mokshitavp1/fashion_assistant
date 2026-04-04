# write a function read_image_file that:
# - accepts an UploadFile from fastapi
# - reads the file bytes
# - converts it to a numpy array
# - decodes it into an OpenCV BGR image
# - raises a clear error if the file is not a valid image
import numpy as np
import cv2
from fastapi import UploadFile, HTTPException
async def read_image_file(file: UploadFile) -> np.ndarray:
    try:
        file_bytes = await file.read()
        np_array = np.frombuffer(file_bytes, np.uint8)
        image = cv2.imdecode(np_array, cv2.IMREAD_COLOR)
        if image is None:
            raise ValueError("Decoded image is None")
        return image
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid image file: {str(e)}")
    
    