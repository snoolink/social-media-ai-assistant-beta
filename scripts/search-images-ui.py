import os
import shutil
import random
import json
from pathlib import Path
from datetime import datetime
import streamlit as st
from PIL import Image
from google import genai
from google.genai import types

# -------------------------
# CONFIG  
# -------------------------
MODEL_NAME = "gemini-2.0-flash-exp"

# Optional: HEIC support
try:
    from pillow_heif import register_heif_opener
    register_heif_opener()
except ImportError:
    st.warning("Install pillow-heif to support .HEIC images.")

# -------------------------
# HELPER FUNCTIONS
# -------------------------
def load_api_key():
    """Load a random API key from creds.json"""
    creds_file = Path(__file__).parent / "creds.json"
    if not creds_file.exists():
        st.error("creds.json not found in script directory.")
        return None
    try:
        with open(creds_file, 'r') as f:
            creds = json.load(f)
        api_keys = creds.get("api_keys", [])
        if not api_keys:
            st.error("No API keys found in creds.json")
            return None
        return random.choice(api_keys)
    except Exception as e:
        st.error(f"Error reading creds.json: {e}")
        return None

def get_mime_type(image_path):
    ext = Path(image_path).suffix.lower()
    return {
        '.jpg':'image/jpeg', '.jpeg':'image/jpeg', '.png':'image/png',
        '.webp':'image/webp', '.gif':'image/gif', '.bmp':'image/bmp', 
        '.heic':'image/heic'
    }.get(ext, 'image/jpeg')

def is_image_file(filename):
    return Path(filename).suffix.lower() in {'.jpg', '.jpeg', '.png', '.webp', '.gif', '.bmp', '.heic'}

def build_prompt(user_query):
    """Convert short user query into a descriptive AI prompt"""
    query = user_query.lower()
    expansions = {
        "man": "a male adult person",
        "woman": "a female adult person",
        "tshirt": "a short-sleeve T-shirt",
        "shirt": "a full-length shirt",
        "solo": "only one person, no other people in the image",
        "ocean": "large body of water, possibly with waves or horizon",
        "boat": "a visible boat in the water",
        "skyline": "city skyline with buildings visible",
        "white": "white-colored",
        "black": "black-colored",
        "red": "red-colored",
        "blue": "blue-colored"
    }
    for k, v in expansions.items():
        query = query.replace(k, v)
    
    prompt = f"""Analyze this image carefully and determine if it matches the following description: "{query}".
- Focus on the main subject of the image.
- Ignore irrelevant background details.
- Answer ONLY "Yes" or "No", followed by a brief explanation."""
    
    return prompt

def analyze_image(image_path, client, user_query=""):
    """Return True if image matches the query, False otherwise"""
    try:
        from io import BytesIO
        with Image.open(image_path) as img:
            img_rgb = img.convert("RGB")
            buf = BytesIO()
            img_rgb.save(buf, format='JPEG')
            image_bytes = buf.getvalue()

        mime_type = get_mime_type(image_path)
        image_part = types.Part.from_bytes(data=image_bytes, mime_type=mime_type)

        prompt = build_prompt(user_query)
        
        response = client.models.generate_content(
            model=MODEL_NAME,
            contents=[prompt, image_part]
        )
        text = response.text.strip()
        is_match = text.lower().startswith("yes")
        return is_match, text
    except Exception as e:
        return False, str(e)

# -------------------------
# STREAMLIT UI
# -------------------------
st.set_page_config(page_title="AI Image Search & Selection", layout="wide")
st.title("🖼️ AI Image Search & Selection")
st.write("""
Search images using natural language, select them by clicking on thumbnails,  
and save selected images to a folder named after your query and timestamp.
""")

# Sidebar: input/output folders and API key
input_folder = st.sidebar.text_input("Input Folder Path", value="./images")
output_base = st.sidebar.text_input("Output Base Folder", value="./selected_images")
st.sidebar.markdown("### API Key")
api_key = st.sidebar.text_input("Paste your Gemini API key here (or leave blank to pick randomly)")

if not api_key:
    api_key = load_api_key()
    if api_key:
        st.sidebar.success("Using a random API key from creds.json")
    else:
        st.sidebar.warning("No API key available. Please enter one.")
        st.stop()

client = genai.Client(api_key=api_key)

# -------------------------
# Search Query
# -------------------------
search_query = st.text_input("Enter search query (e.g., 'rolled sleeves', 'white tshirt', 'ocean with boat'):")

if st.button("Run Search"):
    if not os.path.exists(input_folder):
        st.error(f"Input folder '{input_folder}' not found")
        st.stop()
    
    all_images = [f for f in Path(input_folder).iterdir() if f.is_file() and is_image_file(f.name)]
    if not all_images:
        st.warning("No images found in folder.")
        st.stop()
    
    st.info(f"Found {len(all_images)} images. Running AI analysis...")

    detected_images = []
    progress_bar = st.progress(0)

    for i, img_path in enumerate(all_images):
        is_match, explanation = analyze_image(img_path, client, search_query)
        if is_match:
            detected_images.append((img_path, explanation))
        progress_bar.progress((i + 1) / len(all_images))

    st.success(f"Analysis complete. {len(detected_images)} images matched your query.")

    # -------------------------
    # Display images with clickable selection
    # -------------------------
    selected_images = st.session_state.get("selected_images", [])

    if detected_images:
        st.markdown("### Click on images to select/deselect")
        cols = st.columns(5)
        for i, (img_path, explanation) in enumerate(detected_images):
            with cols[i % 5]:
                is_selected = img_path in selected_images
                if st.button(
                    Path(img_path).name + (" ✅" if is_selected else ""),
                    key=f"imgbtn_{i}"
                ):
                    if is_selected:
                        selected_images.remove(img_path)
                    else:
                        selected_images.append(img_path)
                st.image(img_path, use_container_width=True)
        st.session_state.selected_images = selected_images

    # -------------------------
    # Save selected images
    # -------------------------
    if selected_images:
        if st.button("Save Selected Images"):
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            folder_name = f"{search_query.replace(' ','_')}_{timestamp}"
            save_path = Path(output_base) / folder_name
            os.makedirs(save_path, exist_ok=True)
            for img_path in selected_images:
                shutil.copy(img_path, save_path)
            st.success(f"{len(selected_images)} images saved to folder: {save_path}")
