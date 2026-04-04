
# write a function find_matching_wardrobe_items that:
# - accepts new_item_color (string), new_item_category (string), wardrobe_items (list of WardrobeItem)
# - categorizes wardrobe items
# - finds items that can pair with the new item (tops pair with bottoms, etc.)
# - checks color harmony between new item and each potential match
# - returns list of compatible items with harmony scores

# write a function calculate_wardrobe_compatibility_score that:
# - accepts matching_items (list from find_matching_wardrobe_items)
# - calculates percentage of wardrobe that matches the new item
# - returns compatibility score (0-1) and match count

# write a function check_duplicate_in_wardrobe that:
# - accepts new_item_color (string), new_item_type (string), wardrobe_items (list)
# - checks if user already has similar item (same color and type)
# - returns dict with: is_duplicate (bool), similar_items (list)

# write a function generate_purchase_recommendation that:
# - accepts compatibility_score (float), is_duplicate (bool), body_shape_score (float), matching_items_count (int)
# - combines all factors to decide: "buy", "maybe", or "skip"
# - "buy" if compatibility > 0.6 and not duplicate and body_shape_score > 0.7
# - "skip" if compatibility < 0.4 or is duplicate or body_shape_score < 0.4
# - "maybe" for everything else
# - returns recommendation (string) and reasons (list of strings)

# write a function analyze_shopping_item that:
# - accepts image (cv2.Mat), wardrobe_items (list), user_body_shape (string), user_undertone (string)
# - classifies the new clothing item using classify_clothing
# - finds matching wardrobe items
# - calculates compatibility score
# - checks for duplicates
# - checks body shape compatibility
# - generates purchase recommendation
# - returns comprehensive analysis dict with: classification, matches, compatibility, recommendation, reasons
from typing import List, Dict, Optional
from database.models import WardrobeItem
from services.clothing_classifier import classify_clothing
from services.color_harmony import check_color_harmony
from services.outfit_generator import parse_rgb_from_string, categorize_wardrobe_items
from services.body_shape_rules import get_body_shape_score
import cv2

def find_matching_wardrobe_items(
    new_item_color: str,
    new_item_category: str,
    wardrobe_items: List[WardrobeItem]
) -> List[Dict]:
    """
    Find wardrobe items that can pair with the new item.
    
    Args:
        new_item_color: Color of the new item
        new_item_category: Category (top, bottom, dress, etc.)
        wardrobe_items: User's existing wardrobe
        
    Returns:
        List of compatible items with harmony scores
    """
    categorized_items = categorize_wardrobe_items(wardrobe_items)
    potential_matches = []
    
    # Find complementary categories
    if new_item_category == "top":
        potential_matches = categorized_items.get("bottom", [])
    elif new_item_category == "bottom":
        potential_matches = categorized_items.get("top", [])
    elif new_item_category == "dress":
        # Dresses can match with accessories
        potential_matches = categorized_items.get("accessories", [])
    else:
        # Accessories can match with tops and bottoms
        potential_matches = categorized_items.get("top", []) + categorized_items.get("bottom", [])
    
    matching_items = []
    new_rgb = parse_rgb_from_string(new_item_color)
    
    for item in potential_matches:
        item_rgb = parse_rgb_from_string(item.color_primary)
        harmony = check_color_harmony(new_rgb, item_rgb)
        
        if harmony["compatible"]:
            matching_items.append({
                "item_id": item.id,
                "item_type": item.clothing_type,
                "item_color": item.color_primary,
                "item_category": item.category,
                "harmony_type": harmony["harmony_type"],
                "harmony_score": harmony["score"]
            })
    
    return matching_items

def calculate_wardrobe_compatibility_score(
    matching_items: List[Dict],
    total_relevant_items: int
) -> Dict:
    """
    Calculate how well the new item fits with existing wardrobe.
    
    Args:
        matching_items: Items that match from find_matching_wardrobe_items
        total_relevant_items: Total items in relevant categories
        
    Returns:
        dict: compatibility_score (float), match_count (int)
    """
    if total_relevant_items == 0:
        return {"compatibility_score": 0.0, "match_count": 0}
    
    match_count = len(matching_items)
    
    # Calculate compatibility as percentage of wardrobe that matches
    compatibility_score = min(match_count / max(total_relevant_items, 1), 1.0)
    
    # Boost score slightly if there are any good matches
    if match_count > 0:
        # Average harmony score of matches
        avg_harmony = sum(item["harmony_score"] for item in matching_items) / match_count
        compatibility_score = (compatibility_score + avg_harmony) / 2
    
    return {
        "compatibility_score": round(compatibility_score, 2),
        "match_count": match_count
    }

def check_duplicate_in_wardrobe(
    new_item_color: str,
    new_item_type: str,
    wardrobe_items: List[WardrobeItem]
) -> Dict:
    """
    Check if user already owns a similar item.
    
    Args:
        new_item_color: Color of new item
        new_item_type: Type of new item
        wardrobe_items: Existing wardrobe
        
    Returns:
        dict: is_duplicate (bool), similar_items (list)
    """
    similar_items = []
    
    for item in wardrobe_items:
        # Check for exact match (same color and type)
        if (item.color_primary.lower() == new_item_color.lower() and 
            item.clothing_type.lower() == new_item_type.lower()):
            similar_items.append({
                "item_id": item.id,
                "item_type": item.clothing_type,
                "item_color": item.color_primary
            })
    
    return {
        "is_duplicate": len(similar_items) > 0,
        "similar_items": similar_items
    }

def generate_purchase_recommendation(
    compatibility_score: float,
    is_duplicate: bool,
    body_shape_score: float,
    matching_items_count: int
) -> Dict:
    """
    Generate buy/skip recommendation based on all factors.
    
    Args:
        compatibility_score: How well item fits with wardrobe (0-1)
        is_duplicate: Whether user already owns similar item
        body_shape_score: How well item flatters body shape (0-1)
        matching_items_count: Number of items it can pair with
        
    Returns:
        dict: recommendation ("buy", "maybe", "skip"), reasons (list)
    """
    reasons = []
    
    # Analyze each factor
    if is_duplicate:
        reasons.append("⚠️ You already own a similar item")
    
    if body_shape_score >= 0.8:
        reasons.append("✅ Flattering for your body shape")
    elif body_shape_score < 0.4:
        reasons.append("❌ Not recommended for your body shape")
    
    if compatibility_score >= 0.6:
        reasons.append(f"✅ Pairs well with {matching_items_count} item(s) in your wardrobe")
    elif compatibility_score < 0.3:
        reasons.append(f"⚠️ Limited pairing options - only {matching_items_count} match(es)")
    
    if matching_items_count == 0:
        reasons.append("❌ Doesn't match any items in your wardrobe")
    
    # Decision logic
    if is_duplicate:
        recommendation = "skip"
        reasons.append("💡 Consider something different to diversify your wardrobe")
    elif compatibility_score >= 0.6 and body_shape_score >= 0.7 and matching_items_count > 0:
        recommendation = "buy"
        reasons.append("🎉 This is a great addition to your wardrobe!")
    elif compatibility_score < 0.3 or body_shape_score < 0.4 or matching_items_count == 0:
        recommendation = "skip"
        reasons.append("💡 Look for items that better match your style profile")
    else:
        recommendation = "maybe"
        reasons.append("🤔 Decent option, but not perfect - consider your budget and needs")
    
    return {
        "recommendation": recommendation,
        "reasons": reasons
    }

def analyze_shopping_item(
    image: cv2.Mat,
    wardrobe_items: List[WardrobeItem],
    user_body_shape: str,
    user_undertone: str
) -> Dict:
    """
    Complete analysis of a shopping item.
    
    Args:
        image: Photo of the item being considered
        wardrobe_items: User's existing wardrobe
        user_body_shape: User's body shape
        user_undertone: User's undertone
        
    Returns:
        Comprehensive analysis with purchase recommendation
    """
    # Step 1: Classify the new item
    classification = classify_clothing(image)
    
    new_item_color = classification["color_primary"]
    new_item_type = classification["type"]
    new_item_category = "top" if new_item_type in ["shirt", "dress"] else "bottom"
    
    # Step 2: Find matching wardrobe items
    matching_items = find_matching_wardrobe_items(
        new_item_color=new_item_color,
        new_item_category=new_item_category,
        wardrobe_items=wardrobe_items
    )
    
    # Step 3: Calculate compatibility
    categorized = categorize_wardrobe_items(wardrobe_items)
    if new_item_category == "top":
        total_relevant = len(categorized.get("bottom", []))
    elif new_item_category == "bottom":
        total_relevant = len(categorized.get("top", []))
    else:
        total_relevant = len(wardrobe_items)
    
    compatibility = calculate_wardrobe_compatibility_score(
        matching_items=matching_items,
        total_relevant_items=total_relevant
    )
    
    # Step 4: Check for duplicates
    duplicate_check = check_duplicate_in_wardrobe(
        new_item_color=new_item_color,
        new_item_type=new_item_type,
        wardrobe_items=wardrobe_items
    )
    
    # Step 5: Check body shape compatibility
    body_shape_score = get_body_shape_score(
        body_shape=user_body_shape,
        clothing_type=new_item_type,
        category=new_item_category
    )
    
    # Step 6: Generate recommendation
    recommendation = generate_purchase_recommendation(
        compatibility_score=compatibility["compatibility_score"],
        is_duplicate=duplicate_check["is_duplicate"],
        body_shape_score=body_shape_score,
        matching_items_count=compatibility["match_count"]
    )
    
    return {
        "item_classification": {
            "type": new_item_type,
            "category": new_item_category,
            "color_primary": new_item_color,
            "color_secondary": classification["color_secondary"],
            "pattern": classification["pattern"]
        },
        "wardrobe_compatibility": {
            "score": compatibility["compatibility_score"],
            "matching_items_count": compatibility["match_count"],
            "matching_items": matching_items[:5]  # Top 5 matches
        },
        "duplicate_check": duplicate_check,
        "body_shape_compatibility": {
            "score": round(body_shape_score, 2),
            "body_shape": user_body_shape
        },
        "recommendation": recommendation["recommendation"],
        "reasons": recommendation["reasons"]
    }