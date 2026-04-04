"""Rule-based outfit generator for the fashion app — deterministic heuristics, no ML/API calls."""
APP_NAME = "fashion"

# Import necessary modules
# from typing import List, Dict, Optional
# from itertools import combinations
# from database.models import WardrobeItem
# from services.color_harmony import check_color_harmony, calculate_outfit_color_score
# from services.body_shape_rules import calculate_outfit_body_shape_score

# write a function categorize_wardrobe_items that:
# - accepts a list of WardrobeItem objects
# - groups items by category (tops, bottoms, dresses, shoes, accessories)
# - returns a dictionary with category as key and list of items as value

# write a function parse_rgb_from_string that:
# - accepts a color string like "red", "blue", etc.
# - maps common color names to approximate RGB values
# - returns an RGB tuple (r, g, b)
# - handles cases where input might already be RGB-like

# write a function calculate_outfit_score that:
# - accepts body_shape (string), undertone (string), and items (list of dicts with color_primary, type, category)
# - calculates color harmony score using calculate_outfit_color_score
# - calculates body shape score using calculate_outfit_body_shape_score
# - calculates undertone compatibility (warm undertone with warm colors = bonus, etc.)
# - combines all scores with weights: color_score * 0.4 + body_shape_score * 0.4 + undertone_score * 0.2
# - returns overall outfit score (0-1)

# write a function generate_outfit_combinations that:
# - accepts categorized_items (dict from categorize_wardrobe_items)
# - generates possible outfit combinations:
#   * Option 1: top + bottom (+ optional accessories/shoes)
#   * Option 2: dress (+ optional accessories/shoes)
# - limits to maximum 20 combinations to avoid performance issues
# - returns a list of outfit combinations (each is a list of WardrobeItem objects)

# write a function generate_outfits that:
# - accepts wardrobe_items (list of WardrobeItem), body_shape (string), undertone (string)
# - accepts optional filters: occasion (string), season (string), min_score (float)
# - categorizes wardrobe items
# - generates outfit combinations
# - scores each outfit using calculate_outfit_score
# - filters by min_score (default 0.6)
# - filters by season and occasion if provided
# - sorts by score (highest first)
# - returns top 10 outfits as list of dicts with: items, score, color_score, body_shape_score

# write a function get_outfit_recommendations that:
# - accepts db session, user_id, optional occasion, season, limit
# - gets user profile (body_shape, undertone) from database
# - gets user's wardrobe items from database
# - calls generate_outfits
# - returns formatted outfit recommendations with item details
from typing import List, Dict, Optional
from itertools import combinations
from database.models import WardrobeItem
from services.color_harmony import calculate_outfit_color_score, get_color_temperature
from services.body_shape_rules import calculate_outfit_body_shape_score

# Color name to RGB mapping
COLOR_MAP = {
    "red": (255, 0, 0),
    "blue": (0, 0, 255),
    "green": (0, 255, 0),
    "yellow": (255, 255, 0),
    "orange": (255, 165, 0),
    "purple": (128, 0, 128),
    "pink": (255, 192, 203),
    "brown": (165, 42, 42),
    "black": (0, 0, 0),
    "white": (255, 255, 255),
    "gray": (128, 128, 128),
    "grey": (128, 128, 128),
    "beige": (245, 245, 220),
    "navy": (0, 0, 128),
    "teal": (0, 128, 128),
    "maroon": (128, 0, 0),
    "olive": (128, 128, 0),
}

OCCASION_RULES = {
    "casual": {
        "preferred_categories": {"top", "bottom", "dress", "shoes"},
        "avoid_patterns": {"formal", "party"},
    },
    "work": {
        "preferred_categories": {"top", "bottom", "dress", "shoes"},
        "avoid_patterns": {"party", "athleisure"},
    },
    "formal": {
        "preferred_categories": {"dress", "top", "bottom", "shoes", "accessories"},
        "avoid_patterns": {"athleisure", "casual"},
    },
    "party": {
        "preferred_categories": {"dress", "top", "bottom", "shoes", "accessories"},
        "avoid_patterns": {"work", "athleisure"},
    },
    "sport": {
        "preferred_categories": {"top", "bottom", "shoes"},
        "avoid_patterns": {"formal", "work"},
    },
}


def normalize_occasion(occasion: Optional[str]) -> Optional[str]:
    if not occasion:
        return None
    raw = occasion.strip().lower()
    aliases = {
        "office": "work",
        "business": "work",
        "wedding": "formal",
        "event": "formal",
        "gym": "sport",
        "sports": "sport",
    }
    return aliases.get(raw, raw)


def infer_item_occasion_tags(item: WardrobeItem) -> set:
    tags = set()

    category = (item.category or "").strip().lower()
    clothing_type = (item.clothing_type or "").strip().lower()
    pattern = (item.pattern or "").strip().lower()

    if category in {"dress", "accessories"} and pattern in {"solid", "floral", "striped", "checked"}:
        tags.update({"formal", "party"})

    if category in {"top", "bottom", "shoes"}:
        tags.update({"casual", "work"})

    if any(word in clothing_type for word in ["blazer", "shirt", "trouser", "oxford"]):
        tags.add("work")
    if any(word in clothing_type for word in ["gown", "suit", "heel", "loafer"]):
        tags.add("formal")
    if any(word in clothing_type for word in ["sneaker", "jogger", "hoodie", "track"]):
        tags.add("sport")
        tags.add("casual")

    if not tags:
        tags.add("casual")

    return tags


def calculate_occasion_compatibility(occasion: str, outfit_items: List[WardrobeItem]) -> float:
    normalized = normalize_occasion(occasion)
    if not normalized or normalized not in OCCASION_RULES:
        return 0.75

    rules = OCCASION_RULES[normalized]
    preferred_categories = rules["preferred_categories"]
    avoid_patterns = rules["avoid_patterns"]

    if not outfit_items:
        return 0.0

    score = 0.0
    for item in outfit_items:
        category = (item.category or "").strip().lower()
        pattern = (item.pattern or "").strip().lower()
        item_tags = infer_item_occasion_tags(item)

        if normalized in item_tags:
            score += 1.0
        elif category in preferred_categories:
            score += 0.7
        else:
            score += 0.3

        if pattern and pattern in avoid_patterns:
            score -= 0.25

    return max(0.0, min(score / len(outfit_items), 1.0))

def categorize_wardrobe_items(items: List[WardrobeItem]) -> Dict[str, List[WardrobeItem]]:
    """Group wardrobe items by category"""
    categories = {
        "top": [],
        "bottom": [],
        "dress": [],
        "shoes": [],
        "accessories": []
    }
    
    for item in items:
        category = item.category.lower() if item.category else "accessories"
        if category in categories:
            categories[category].append(item)
        else:
            categories["accessories"].append(item)
    
    return categories

def parse_rgb_from_string(color_string: str) -> tuple:
    """Convert color name to RGB tuple"""
    color_lower = color_string.lower().strip()
    return COLOR_MAP.get(color_lower, (128, 128, 128))  # Default to gray

def calculate_undertone_compatibility(undertone: str, colors: List[tuple]) -> float:
    """Calculate how well colors match the user's undertone"""
    if not undertone or not colors:
        return 0.7  # Neutral score
    
    undertone = undertone.lower()
    compatible_count = 0
    
    for color in colors:
        color_temp = get_color_temperature(color)
        
        # Warm undertone works well with warm colors
        if undertone == "warm" and color_temp == "warm":
            compatible_count += 1
        # Cool undertone works well with cool colors
        elif undertone == "cool" and color_temp == "cool":
            compatible_count += 1
        # Neutral undertone works with everything
        elif undertone == "neutral":
            compatible_count += 0.5
        # Neutral colors work with any undertone
        elif color_temp == "neutral":
            compatible_count += 0.5
    
    return min(compatible_count / len(colors), 1.0)

def calculate_outfit_score(
    body_shape: str,
    undertone: str,
    items: List[Dict]
) -> Dict[str, float]:
    """Calculate overall outfit score based on multiple factors"""
    
    # Extract colors from items
    colors = []
    for item in items:
        color_rgb = parse_rgb_from_string(item.get("color_primary", "gray"))
        colors.append(color_rgb)
    
    # Calculate individual scores
    color_score = calculate_outfit_color_score(colors) if len(colors) > 1 else 1.0
    body_shape_score = calculate_outfit_body_shape_score(body_shape, items)
    undertone_score = calculate_undertone_compatibility(undertone, colors)
    
    # Weighted overall score
    overall_score = (color_score * 0.4) + (body_shape_score * 0.4) + (undertone_score * 0.2)
    
    return {
        "overall": overall_score,
        "color": color_score,
        "body_shape": body_shape_score,
        "undertone": undertone_score
    }

def generate_outfit_combinations(categorized_items: Dict[str, List[WardrobeItem]]) -> List[List[WardrobeItem]]:
    """Generate possible outfit combinations"""
    outfits = []
    
    tops = categorized_items.get("top", [])
    bottoms = categorized_items.get("bottom", [])
    dresses = categorized_items.get("dress", [])
    
    # Combination 1: Top + Bottom
    for top in tops[:10]:  # Limit to avoid too many combinations
        for bottom in bottoms[:10]:
            outfits.append([top, bottom])
    
    # Combination 2: Dress alone
    for dress in dresses[:10]:
        outfits.append([dress])
    
    # Limit total combinations
    return outfits[:20]

def generate_outfits(
    wardrobe_items: List[WardrobeItem],
    body_shape: str,
    undertone: str,
    occasion: Optional[str] = None,
    season: Optional[str] = None,
    min_score: float = 0.55
) -> List[Dict]:
    """Generate and score outfit recommendations"""
    
    if not wardrobe_items:
        return []
    
    # Categorize items
    categorized = categorize_wardrobe_items(wardrobe_items)
    
    # Generate combinations
    combinations = generate_outfit_combinations(categorized)
    
    normalized_occasion = normalize_occasion(occasion)

    # Score each outfit
    scored_outfits = []
    all_scored_outfits = []
    for outfit_items in combinations:
        # Filter by season if specified
        if season:
            if not all(item.season in [season, "all", None] for item in outfit_items):
                continue
        
        # Convert items to dict format for scoring
        items_dict = [
            {
                "type": item.clothing_type,
                "category": item.category,
                "color_primary": item.color_primary
            }
            for item in outfit_items
        ]
        
        # Calculate scores
        scores = calculate_outfit_score(body_shape, undertone, items_dict)

        occasion_score = calculate_occasion_compatibility(normalized_occasion, outfit_items) if normalized_occasion else 0.75

        weighted_score = (scores["overall"] * 0.85) + (occasion_score * 0.15)

        # Enforce minimum occasion quality when user explicitly asks for occasion
        if normalized_occasion and occasion_score < 0.45:
            continue
        
        candidate = {
            "items": outfit_items,
            "score": weighted_score,
            "color_score": scores["color"],
            "body_shape_score": scores["body_shape"],
            "undertone_score": scores["undertone"],
            "occasion_score": occasion_score,
            "occasion": normalized_occasion,
        }

        all_scored_outfits.append(candidate)

        # Filter by minimum score
        if weighted_score >= min_score:
            scored_outfits.append(candidate)
    
    # Sort by score (highest first)
    scored_outfits.sort(key=lambda x: x["score"], reverse=True)

    # Fallback: when all outfits are below threshold, still return the best options
    # so users with small wardrobes don't see an empty recommendation screen.
    if not scored_outfits and all_scored_outfits:
        all_scored_outfits.sort(key=lambda x: x["score"], reverse=True)
        return all_scored_outfits[:10]
    
    # Return top 10
    return scored_outfits[:10]

def get_outfit_recommendations(
    wardrobe_items: List[WardrobeItem],
    user_body_shape: str,
    user_undertone: str,
    occasion: Optional[str] = None,
    season: Optional[str] = None,
    limit: int = 10
) -> List[Dict]:
    """Get formatted outfit recommendations for a user"""
    
    outfits = generate_outfits(
        wardrobe_items=wardrobe_items,
        body_shape=user_body_shape,
        undertone=user_undertone,
        occasion=occasion,
        season=season
    )
    
    # Format response
    recommendations = []
    for idx, outfit in enumerate(outfits[:limit]):
        recommendations.append({
            "outfit_number": idx + 1,
            "overall_score": round(outfit["score"], 2),
            "color_harmony_score": round(outfit["color_score"], 2),
            "body_shape_score": round(outfit["body_shape_score"], 2),
            "undertone_score": round(outfit["undertone_score"], 2),
            "occasion_score": round(outfit.get("occasion_score", 0.75), 2),
            "occasion": outfit.get("occasion"),
            "items": [
                {
                    "id": item.id,
                    "type": item.clothing_type,
                    "category": item.category,
                    "color": item.color_primary,
                    "pattern": item.pattern,
                    "image_path": item.image_path
                }
                for item in outfit["items"]
            ]
        })
    
    return recommendations

def is_ai_based() -> bool:
	"""Return False: this module uses rule-based scoring and combinations, not ML or external AI APIs."""
	return False

def list_ai_indicators() -> List[str]:
	"""Common keywords/files/deps to search for elsewhere in the repo to detect AI usage."""
	return [
		"openai",
		"api.openai.com",
		"transformers",
		"torch",
		"tensorflow",
		"sklearn",
		"model.predict",
		"inference",
		"huggingface",
		"GPT",
		"llm",
	]