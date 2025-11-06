"""
query_expander.py

Helper script to expand short user queries into detailed semantic search descriptions.
Uses Gemini API to generate comprehensive image search criteria.
"""

import json
import random
from pathlib import Path
from google import genai

MODEL_NAME = "gemini-2.0-flash-exp"

def load_api_key():
    """Load a random API key from creds.json"""
    creds_file = Path(__file__).parent / "creds.json"
    if not creds_file.exists():
        raise FileNotFoundError("creds.json not found in script directory.")
    
    with open(creds_file, 'r') as f:
        creds = json.load(f)
    
    api_keys = creds.get("api_keys", [])
    if not api_keys:
        raise ValueError("No API keys found in creds.json")
    
    return random.choice(api_keys)


EXPANSION_PROMPT = """You are an expert at creating detailed image search descriptions. 

Given a SHORT user query about what they want to find in photos, expand it into a COMPREHENSIVE, DETAILED description that an AI vision model can use to accurately identify matching images.

User Query: "{query}"

Your expanded description should:
1. **Be specific and detailed** - Include exact visual characteristics
2. **Define what TO include** - Clearly describe what should be present
3. **Define what to EXCLUDE** - List similar things that should NOT match
4. **Cover edge cases** - Handle ambiguous scenarios
5. **Use clear visual language** - Focus on what's visible in the image
6. **Be 2-4 sentences long** - Comprehensive but concise

Examples:

User: "rolled sleeves"
Expanded: "Find images of a person wearing a long-sleeve shirt (dress shirt, button-up, or casual shirt). The sleeves must be rolled up past the wrist with forearms clearly visible. Exclude t-shirts, polos, short-sleeve shirts, tank tops, sleeveless garments, and images where sleeves are only slightly pushed up."

User: "only upper body visible"
Expanded: "Photos where the upper body of a person is clearly visible, including the torso, arms, and shoulders. The image should be cropped or framed from the waist or chest upward, not showing the full body or legs. Exclude distant shots, full-body photos, or extreme close-up face-only portraits."

User: "solo man standing"
Expanded: "Find images containing exactly one adult male person in a standing position. The man should be the main subject and clearly identifiable. Exclude images with multiple people, seated individuals, children, or images where the person is lying down or in other positions."

User: "ocean"
Expanded: "Images showing a large body of ocean or sea water as a prominent element. Should include visible water (calm or with waves), horizon line, or coastal features. Exclude swimming pools, lakes, rivers, or images where water is only a minor background element."

User: "blue denim jacket"
Expanded: "Find images of a person wearing a blue denim jacket (jean jacket). The jacket should be clearly visible and identifiable as denim material with blue coloring. Exclude denim shirts, vests, pants, or jackets in other colors like black or white denim."

User: "two men in frame"
Expanded: "Images containing exactly two adult male persons visible in the frame. Both men should be clearly identifiable as the main subjects. Exclude images with only one man, three or more people, images with women, or distant shots where people are barely visible."

User: "boy and girl"
Expanded: "Photos showing one boy and one girl together (children or young adults). Both should be clearly visible as the main subjects. Exclude images with only one child, multiple children of the same gender, adult men and women, or groups with more than two people."

Now expand this user query:
User: "{query}"
Expanded:"""


def expand_query(user_query: str, api_key: str = None) -> str:
    """
    Expand a short user query into a detailed semantic search description.
    
    Args:
        user_query: Short phrase from user (e.g., "rolled sleeves")
        api_key: Optional API key. If None, loads from creds.json
    
    Returns:
        Detailed expanded description for semantic search
    """
    if not api_key:
        api_key = load_api_key()
    
    client = genai.Client(api_key=api_key)
    
    prompt = EXPANSION_PROMPT.format(query=user_query)
    
    try:
        response = client.models.generate_content(
            model=MODEL_NAME,
            contents=[prompt]
        )
        
        expanded = response.text.strip()
        
        # Remove any "Expanded:" prefix if the model adds it
        if expanded.lower().startswith("expanded:"):
            expanded = expanded[9:].strip()
        
        return expanded
    
    except Exception as e:
        # Fallback: return original query if expansion fails
        print(f"Query expansion failed: {e}")
        return user_query


def expand_query_with_cache(user_query: str, api_key: str = None, cache_file: str = "query_cache.json") -> str:
    """
    Expand query with caching to avoid repeated API calls for same queries.
    
    Args:
        user_query: Short phrase from user
        api_key: Optional API key
        cache_file: Path to cache file
    
    Returns:
        Expanded description (from cache or fresh API call)
    """
    cache_path = Path(__file__).parent / cache_file
    
    # Load cache
    cache = {}
    if cache_path.exists():
        try:
            with open(cache_path, 'r') as f:
                cache = json.load(f)
        except:
            cache = {}
    
    # Check cache
    query_key = user_query.lower().strip()
    if query_key in cache:
        print(f"Using cached expansion for: '{user_query}'")
        return cache[query_key]
    
    # Expand and cache
    expanded = expand_query(user_query, api_key)
    cache[query_key] = expanded
    
    # Save cache
    try:
        with open(cache_path, 'w') as f:
            json.dump(cache, f, indent=2)
    except Exception as e:
        print(f"Failed to save cache: {e}")
    
    return expanded


# -------------------------
# CLI Testing Interface
# -------------------------
if __name__ == "__main__":
    import sys
    
    print("🔍 Query Expander - Testing Interface\n")
    
    # Test queries
    test_queries = [
        "ocean",
        "solo man standing",
        "two men in frame",
        "blue denim jacket",
        "person rolling up sleeves",
        "boy and girl",
        "only upper body visible",
        "white tshirt",
        "sunset beach"
    ]
    
    if len(sys.argv) > 1:
        # Use command line argument
        query = " ".join(sys.argv[1:])
        print(f"Query: {query}")
        print(f"\nExpanded: {expand_query_with_cache(query)}")
    else:
        # Run test suite
        print("Running test expansion on sample queries...\n")
        for query in test_queries:
            print(f"📝 Original: {query}")
            expanded = expand_query_with_cache(query)
            print(f"✨ Expanded: {expanded}")
            print("-" * 80)
            print()