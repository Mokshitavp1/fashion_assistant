# Import necessary libraries
# Import numpy as np
# Import math for color calculations

# write a function rgb_to_hsv that:
# - accepts an RGB tuple (r, g, b) with values 0-255
# - converts RGB to HSV color space
# - returns (hue, saturation, value) where hue is 0-360, saturation and value are 0-1

# write a function get_color_temperature that:
# - accepts an RGB tuple
# - determines if color is warm or cool
# - warm colors: red, orange, yellow (hue 0-60 or 300-360)
# - cool colors: green, blue, purple (hue 60-300)
# - returns "warm", "cool", or "neutral"

# write a function colors_are_complementary that:
# - accepts two RGB tuples
# - converts both to HSV
# - checks if hues are opposite on color wheel (180 degrees apart, with tolerance of 30 degrees)
# - returns True if complementary, False otherwise

# write a function colors_are_analogous that:
# - accepts two RGB tuples
# - converts both to HSV
# - checks if hues are adjacent on color wheel (within 30-60 degrees)
# - returns True if analogous, False otherwise

# write a function colors_are_monochromatic that:
# - accepts two RGB tuples
# - converts both to HSV
# - checks if hues are similar (within 15 degrees) but saturation/value differ
# - returns True if monochromatic, False otherwise

# write a function check_color_harmony that:
# - accepts two RGB tuples (color1, color2)
# - checks if colors are complementary, analogous, or monochromatic
# - checks if both are neutral (gray/white/black) - these match everything
# - returns a dictionary with: compatible (bool), harmony_type (string), score (float 0-1)

# write a function calculate_outfit_color_score that:
# - accepts a list of RGB tuples (colors in an outfit)
# - checks pairwise color harmony between all colors
# - returns an overall color harmony score (0-1)
# - higher score means better color combination
def rgb_to_hsv(rgb: tuple) -> tuple:
    r, g, b = [x / 255.0 for x in rgb]
    mx = max(r, g, b)
    mn = min(r, g, b)
    df = mx - mn
    if df == 0:
        h = 0
    elif mx == r:
        h = (60 * ((g - b) / df) + 360) % 360
    elif mx == g:
        h = (60 * ((b - r) / df) + 120) % 360
    elif mx == b:
        h = (60 * ((r - g) / df) + 240) % 360
    s = 0 if mx == 0 else df / mx
    v = mx
    return (h, s, v)
def get_color_temperature(rgb: tuple) -> str:
    h, s, v = rgb_to_hsv(rgb)
    if s < 0.1 and v > 0.9:
        return "neutral"
    if (h >= 0 and h <= 60) or (h >= 300 and h <= 360):
        return "warm"
    elif h >= 60 and h <= 300:
        return "cool"
    return "neutral"
def colors_are_complementary(rgb1: tuple, rgb2: tuple) -> bool:
    h1, s1, v1 = rgb_to_hsv(rgb1)
    h2, s2, v2 = rgb_to_hsv(rgb2)
    return abs((h1 - h2 + 180) % 360 - 180) <= 30 
def colors_are_analogous(rgb1: tuple, rgb2: tuple) -> bool:
    h1, s1, v1 = rgb_to_hsv(rgb1)
    h2, s2, v2 = rgb_to_hsv(rgb2)
    return abs(h1 - h2) <= 60   
def colors_are_monochromatic(rgb1: tuple, rgb2: tuple) -> bool:
    h1, s1, v1 = rgb_to_hsv(rgb1)
    h2, s2, v2 = rgb_to_hsv(rgb2)
    return abs(h1 - h2) <= 15 and (abs(s1 - s2) > 0.1 or abs(v1 - v2) > 0.1)    
def check_color_harmony(rgb1: tuple, rgb2: tuple) -> dict:
    temp1 = get_color_temperature(rgb1)
    temp2 = get_color_temperature(rgb2)
    
    if temp1 == "neutral" or temp2 == "neutral":
        return {"compatible": True, "harmony_type": "neutral", "score": 1.0}
    
    if colors_are_complementary(rgb1, rgb2):
        return {"compatible": True, "harmony_type": "complementary", "score": 1.0}
    elif colors_are_analogous(rgb1, rgb2):
        return {"compatible": True, "harmony_type": "analogous", "score": 0.8}
    elif colors_are_monochromatic(rgb1, rgb2):
        return {"compatible": True, "harmony_type": "monochromatic", "score": 0.7}
    else:
        return {"compatible": False, "harmony_type": "none", "score": 0.0}  
def calculate_outfit_color_score(colors: list) -> float:
    if len(colors) < 2:
        return 1.0  
    
    total_score = 0.0
    comparisons = 0
    
    for i in range(len(colors)):
        for j in range(i + 1, len(colors)):
            harmony = check_color_harmony(colors[i], colors[j])
            total_score += harmony["score"]
            comparisons += 1
            
    if comparisons == 0:
        return 0.0
    
    return total_score / comparisons    

