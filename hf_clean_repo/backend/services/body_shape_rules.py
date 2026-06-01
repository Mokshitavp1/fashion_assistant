# Import typing for type hints
# from typing import Dict, List

# Define body shape flattering rules as a dictionary

# write a constant BODY_SHAPE_RULES that:
# - is a dictionary mapping body shapes to flattering clothing rules
# - for each body shape (rectangle, pear, inverted_triangle, hourglass, apple), define:
#   * flattering_tops: list of top types that flatter this shape
#   * flattering_bottoms: list of bottom types that flatter this shape
#   * avoid_tops: list of top types to avoid
#   * avoid_bottoms: list of bottom types to avoid
#   * style_tips: list of style tips for this body shape

# Example structure:
# BODY_SHAPE_RULES = {
#     "rectangle": {
#         "flattering_tops": ["fitted", "peplum", "wrap"],
#         "flattering_bottoms": ["bootcut", "wide_leg"],
#         "avoid_tops": ["boxy", "straight"],
#         "avoid_bottoms": ["straight_leg"],
#         "style_tips": ["Add curves with belts", "Create waist definition"]
#     },
#     ... (add other shapes)
# }

# write a function is_flattering_for_body_shape that:
# - accepts body_shape (string), clothing_type (string), category (string: "top" or "bottom")
# - checks if clothing_type is in the flattering list for that body shape and category
# - returns True if flattering, False otherwise
# - returns True by default if body_shape is not in BODY_SHAPE_RULES

# write a function get_body_shape_score that:
# - accepts body_shape (string), clothing_type (string), category (string)
# - returns 1.0 if clothing is in flattering list
# - returns 0.3 if clothing is in avoid list
# - returns 0.7 for neutral (neither flattering nor avoid)

# write a function calculate_outfit_body_shape_score that:
# - accepts body_shape (string) and a list of items (each item is a dict with "type" and "category")
# - calculates average body shape score across all items
# - returns overall body shape compatibility score (0-1)
BODY_SHAPE_RULES = {
    "rectangle": {
        "flattering_tops": ["fitted", "peplum", "wrap"],
        "flattering_bottoms": ["bootcut", "wide_leg"],
        "avoid_tops": ["boxy", "straight"],
        "avoid_bottoms": ["straight_leg"],
        "style_tips": ["Add curves with belts", "Create waist definition"]
    },
    "pear": {
        "flattering_tops": ["off-shoulder", "boat neck", "embellished"],
        "flattering_bottoms": ["A-line skirt", "wide_leg"],
        "avoid_tops": ["tight", "cowl neck"],
        "avoid_bottoms": ["skinny jeans"],
        "style_tips": ["Highlight upper body", "Balance proportions"]
    },
    "inverted_triangle": {
        "flattering_tops": ["V-neck", "wrap", "ruffled"],
        "flattering_bottoms": ["bootcut", "A-line skirt"],
        "avoid_tops": ["padded shoulders", "halter neck"],
        "avoid_bottoms": ["skinny jeans"],
        "style_tips": ["Add volume to lower body", "Define waist"]
    },
    "hourglass": {
        "flattering_tops": ["fitted", "wrap", "V-neck"],
        "flattering_bottoms": ["high-waisted", "pencil skirt"],
        "avoid_tops": ["boxy", "cropped"],
        "avoid_bottoms": ["low-rise jeans"],
        "style_tips": ["Emphasize waist", "Show off curves"]
    },
    "apple": {
        "flattering_tops": ["empire waist", "A-line", "V-neck"],
        "flattering_bottoms": ["bootcut", "wide_leg"],
        "avoid_tops": ["tight", "cowl neck"],
        "avoid_bottoms": ["skinny jeans"],
        "style_tips": ["Draw attention away from midsection", "Highlight legs"]
    }
}   
def is_flattering_for_body_shape(body_shape: str, clothing_type: str, category: str) -> bool:
    rules = BODY_SHAPE_RULES.get(body_shape)
    if not rules:
        return True  # Default to True if body shape not found
    
    if category == "top":
        return clothing_type in rules["flattering_tops"]
    elif category == "bottom":
        return clothing_type in rules["flattering_bottoms"]
    
    return True  # Default to True for unknown category 
def get_body_shape_score(body_shape: str, clothing_type: str, category: str) -> float:      
    rules = BODY_SHAPE_RULES.get(body_shape)
    if not rules:
        return 0.7  # Neutral score if body shape not found
    
    if category == "top":
        if clothing_type in rules["flattering_tops"]:
            return 1.0
        elif clothing_type in rules["avoid_tops"]:
            return 0.3
    elif category == "bottom":
        if clothing_type in rules["flattering_bottoms"]:
            return 1.0
        elif clothing_type in rules["avoid_bottoms"]:
            return 0.3
    
    return 0.7  # Neutral score if neither flattering nor avoided
def calculate_outfit_body_shape_score(body_shape: str, items: list) -> float:   
    if not items:
        return 1.0  # Default to perfect score for empty outfit
    
    total_score = 0.0
    for item in items:
        clothing_type = item.get("type")
        category = item.get("category")
        score = get_body_shape_score(body_shape, clothing_type, category)
        total_score += score
    
    overall_score = total_score / len(items)
    return overall_score    
# Example usage:
# outfit_items = [ 

#     {"type": "fitted", "category": "top"},
#     {"type": "bootcut", "category": "bottom"} 
# ]
# score = calculate_outfit_body_shape_score("rectangle", outfit_items)
# print(f"Outfit body shape compatibility score: {score}")  
# Expected output: Outfit body shape compatibility score: 1.0   
