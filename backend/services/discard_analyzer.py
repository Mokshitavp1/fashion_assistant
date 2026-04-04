# Import necessary modules
# from typing import List, Dict
# from database.models import WardrobeItem
# from services.color_harmony import get_color_temperature
# from services.body_shape_rules import get_body_shape_score
# from services.clothing_classifier import rgb_to_color_name
# from services.outfit_generator import parse_rgb_from_string, categorize_wardrobe_items

# write a function check_undertone_compatibility that:
# - accepts item_color (string), user_undertone (string)
# - converts color name to RGB using parse_rgb_from_string
# - gets color temperature using get_color_temperature
# - checks if warm undertone with warm colors (compatible) or cool with cool (compatible)
# - returns a dict with: compatible (bool), score (float 0-1), reason (string)

# write a function check_body_shape_compatibility that:
# - accepts item (WardrobeItem), user_body_shape (string)
# - uses get_body_shape_score to check if item flatters body shape
# - returns a dict with: compatible (bool), score (float), reason (string)
# - score > 0.8 is compatible, < 0.5 is not compatible

# write a function calculate_item_versatility that:
# - accepts item (WardrobeItem), all_items (list of WardrobeItem)
# - categorizes all items using categorize_wardrobe_items
# - counts how many potential outfit combinations the item can create
# - if item is a top, count how many bottoms it can pair with
# - if item is a bottom, count how many tops it can pair with
# - if item is a dress, it's standalone (versatility = 1)
# - returns versatility score (0-1) and potential_outfits count

# write a function analyze_item_for_discard that:
# - accepts item (WardrobeItem), user_body_shape (string), user_undertone (string), all_items (list)
# - checks undertone compatibility
# - checks body shape compatibility
# - calculates versatility
# - combines scores: undertone_score * 0.3 + body_shape_score * 0.4 + versatility_score * 0.3
# - returns dict with: item_id, overall_score, should_discard (bool if score < 0.5), reasons (list of strings)

# write a function get_discard_recommendations that:
# - accepts wardrobe_items (list of WardrobeItem), user_body_shape (string), user_undertone (string)
# - analyzes each item using analyze_item_for_discard
# - filters items with overall_score < 0.5 as discard candidates
# - sorts by score (lowest first - worst items first)
# - returns list of items to discard with detailed reasons
from typing import List, Dict
from database.models import WardrobeItem
from services.color_harmony import get_color_temperature
from services.body_shape_rules import get_body_shape_score
from services.outfit_generator import parse_rgb_from_string, categorize_wardrobe_items

def check_undertone_compatibility(item_color: str, user_undertone: str) -> Dict:
    """
    Check if item color matches user's undertone.
    
    Args:
        item_color: Color name (e.g., "red", "blue")
        user_undertone: User's undertone ("warm", "cool", or "neutral")
        
    Returns:
        dict: compatible (bool), score (float), reason (string)
    """
    if not user_undertone:
        return {"compatible": True, "score": 0.7, "reason": "No undertone data available"}
    
    # Convert color name to RGB
    color_rgb = parse_rgb_from_string(item_color)
    color_temp = get_color_temperature(color_rgb)
    
    user_undertone = user_undertone.lower()
    
    # Neutral colors work with everyone
    if color_temp == "neutral":
        return {
            "compatible": True,
            "score": 1.0,
            "reason": "Neutral color works with any undertone"
        }
    
    # Warm undertone with warm colors
    if user_undertone == "warm" and color_temp == "warm":
        return {
            "compatible": True,
            "score": 1.0,
            "reason": "Warm color complements warm undertone"
        }
    
    # Cool undertone with cool colors
    if user_undertone == "cool" and color_temp == "cool":
        return {
            "compatible": True,
            "score": 1.0,
            "reason": "Cool color complements cool undertone"
        }
    
    # Neutral undertone works with everything
    if user_undertone == "neutral":
        return {
            "compatible": True,
            "score": 0.9,
            "reason": "Neutral undertone works with most colors"
        }
    
    # Mismatched undertone and color temperature
    return {
        "compatible": False,
        "score": 0.3,
        "reason": f"{color_temp.capitalize()} color clashes with {user_undertone} undertone"
    }

def check_body_shape_compatibility(item: WardrobeItem, user_body_shape: str) -> Dict:
    """
    Check if item flatters user's body shape.
    
    Args:
        item: WardrobeItem object
        user_body_shape: User's body shape
        
    Returns:
        dict: compatible (bool), score (float), reason (string)
    """
    if not user_body_shape:
        return {"compatible": True, "score": 0.7, "reason": "No body shape data available"}
    
    score = get_body_shape_score(
        body_shape=user_body_shape,
        clothing_type=item.clothing_type,
        category=item.category
    )
    
    if score >= 0.8:
        return {
            "compatible": True,
            "score": score,
            "reason": f"Flattering for {user_body_shape} body shape"
        }
    elif score >= 0.5:
        return {
            "compatible": True,
            "score": score,
            "reason": f"Neutral fit for {user_body_shape} body shape"
        }
    else:
        return {
            "compatible": False,
            "score": score,
            "reason": f"Not recommended for {user_body_shape} body shape"
        }

def calculate_item_versatility(item: WardrobeItem, all_items: List[WardrobeItem]) -> Dict:
    """
    Calculate how versatile an item is (how many outfits it can create).
    
    Args:
        item: The wardrobe item to analyze
        all_items: All items in the wardrobe
        
    Returns:
        dict: versatility_score (float), potential_outfits (int)
    """
    categorized = categorize_wardrobe_items(all_items)
    
    item_category = item.category.lower() if item.category else "accessories"
    potential_outfits = 0
    
    # Count potential outfit combinations
    if item_category == "top":
        # Can pair with bottoms
        potential_outfits = len(categorized.get("bottom", []))
    elif item_category == "bottom":
        # Can pair with tops
        potential_outfits = len(categorized.get("top", []))
    elif item_category == "dress":
        # Dresses are standalone
        potential_outfits = 1
    else:
        # Accessories can go with any outfit
        tops = len(categorized.get("top", []))
        bottoms = len(categorized.get("bottom", []))
        dresses = len(categorized.get("dress", []))
        potential_outfits = max(tops * bottoms + dresses, 1)
    
    # Calculate versatility score (0-1 scale)
    # More potential outfits = higher versatility
    max_possible = 10  # Normalize against this
    versatility_score = min(potential_outfits / max_possible, 1.0)
    
    return {
        "versatility_score": versatility_score,
        "potential_outfits": potential_outfits
    }

def analyze_item_for_discard(
    item: WardrobeItem,
    user_body_shape: str,
    user_undertone: str,
    all_items: List[WardrobeItem]
) -> Dict:
    """
    Analyze a single item to determine if it should be discarded.
    
    Args:
        item: WardrobeItem to analyze
        user_body_shape: User's body shape
        user_undertone: User's undertone
        all_items: All wardrobe items (for versatility calculation)
        
    Returns:
        dict: Analysis results with scores and recommendations
    """
    # Check undertone compatibility
    undertone_check = check_undertone_compatibility(item.color_primary, user_undertone)
    
    # Check body shape compatibility
    body_shape_check = check_body_shape_compatibility(item, user_body_shape)
    
    # Calculate versatility
    versatility = calculate_item_versatility(item, all_items)
    
    # Calculate overall score (weighted combination)
    overall_score = (
        undertone_check["score"] * 0.3 +
        body_shape_check["score"] * 0.4 +
        versatility["versatility_score"] * 0.3
    )
    
    # Collect reasons for potential discard
    reasons = []
    if not undertone_check["compatible"]:
        reasons.append(undertone_check["reason"])
    if not body_shape_check["compatible"]:
        reasons.append(body_shape_check["reason"])
    if versatility["potential_outfits"] <= 1:
        reasons.append(f"Low versatility - only {versatility['potential_outfits']} potential outfit(s)")
    
    # Determine if should discard
    should_discard = overall_score < 0.5
    
    return {
        "item_id": item.id,
        "item_type": item.clothing_type,
        "item_category": item.category,
        "item_color": item.color_primary,
        "image_path": item.image_path,
        "overall_score": round(overall_score, 2),
        "undertone_score": round(undertone_check["score"], 2),
        "body_shape_score": round(body_shape_check["score"], 2),
        "versatility_score": round(versatility["versatility_score"], 2),
        "potential_outfits": versatility["potential_outfits"],
        "should_discard": should_discard,
        "reasons": reasons if reasons else ["Item works well with your style"]
    }

def get_discard_recommendations(
    wardrobe_items: List[WardrobeItem],
    user_body_shape: str,
    user_undertone: str,
    discard_threshold: float = 0.5
) -> Dict:
    """
    Analyze entire wardrobe and recommend items to discard.
    
    Args:
        wardrobe_items: List of all wardrobe items
        user_body_shape: User's body shape
        user_undertone: User's undertone
        discard_threshold: Score below which items are recommended for discard
        
    Returns:
        dict: Discard recommendations with analysis
    """
    if not wardrobe_items:
        return {
            "total_items": 0,
            "items_to_discard": [],
            "items_to_keep": [],
            "summary": "No items in wardrobe"
        }
    
    # Analyze each item
    analyzed_items = []
    for item in wardrobe_items:
        analysis = analyze_item_for_discard(
            item=item,
            user_body_shape=user_body_shape,
            user_undertone=user_undertone,
            all_items=wardrobe_items
        )
        analyzed_items.append(analysis)
    
    # Separate items to discard vs keep
    items_to_discard = [item for item in analyzed_items if item["should_discard"]]
    items_to_keep = [item for item in analyzed_items if not item["should_discard"]]
    
    # Sort discard items by score (worst first)
    items_to_discard.sort(key=lambda x: x["overall_score"])
    
    # Sort keep items by score (best first)
    items_to_keep.sort(key=lambda x: x["overall_score"], reverse=True)
    
    return {
        "total_items": len(wardrobe_items),
        "items_to_discard": items_to_discard,
        "items_to_keep": items_to_keep,
        "discard_count": len(items_to_discard),
        "keep_count": len(items_to_keep),
        "summary": f"Recommend discarding {len(items_to_discard)} out of {len(wardrobe_items)} items"
    }