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

# Import the query expander
from query_expander import expand_query_with_cache

# -------------------------
# CONFIG  /Users/jay/Desktop/miss-you-india /Users/jay/Downloads/fall-2025
# -------------------------
MODEL_NAME = "gemini-2.0-flash-exp"

# Optional: HEIC support 
try: 
    from pillow_heif import register_heif_opener
    register_heif_opener()
except ImportError:
    st.warning("Install pillow-heif to support .HEIC images.")

# -------------------------
# CUSTOM CSS
# -------------------------
st.markdown("""
<style>
    .image-container {
        position: relative;
        cursor: pointer;
        transition: transform 0.2s ease;
        border-radius: 8px;
        overflow: hidden;
    }
    .image-container:hover {
        transform: scale(1.05);
    }
    .image-selected {
        border: 4px solid #4CAF50;
        box-shadow: 0 0 20px rgba(76, 175, 80, 0.6);
    }
    .image-unselected {
        border: 2px solid transparent;
    }
    .checkmark {
        position: absolute;
        top: 10px;
        right: 10px;
        background-color: #4CAF50;
        color: white;
        border-radius: 50%;
        width: 30px;
        height: 30px;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 20px;
        font-weight: bold;
        z-index: 10;
    }
    .stButton > button {
        width: 100%;
    }
    div[data-testid="stImage"] {
        border-radius: 8px;
    }
    .expanded-query {
        background-color: #f0f2f6;
        padding: 15px;
        border-radius: 8px;
        border-left: 4px solid #4CAF50;
        margin: 10px 0;
    }
</style>
""", unsafe_allow_html=True)

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

def analyze_image(image_path, client, expanded_query=""):
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

        prompt = f"""Analyze this image carefully and determine if it matches the following description:

"{expanded_query}"

Important instructions:
- Focus on the main subject of the image
- Ignore irrelevant background details
- Consider all the criteria mentioned in the description
- Answer ONLY "Yes" or "No", followed by a brief explanation of why it matches or doesn't match"""
        
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
Search images using natural language. Your query will be automatically expanded into a detailed description for better accuracy.
""")

# Sidebar: input/output folders and API key
input_folder = st.sidebar.text_input("Input Folder Path", value="./images")
output_base = st.sidebar.text_input("Output Base Folder", value="./selected_images")
st.sidebar.markdown("### API Key")
api_key = st.sidebar.text_input("Paste your Gemini API key here (or leave blank to pick randomly)", type="password")

if not api_key:
    api_key = load_api_key()
    if api_key:
        st.sidebar.success("Using a random API key from creds.json")
    else:
        st.sidebar.warning("No API key available. Please enter one.")
        st.stop()

client = genai.Client(api_key=api_key)

# Initialize session state
if "detected_images" not in st.session_state:
    st.session_state.detected_images = []
if "selected_images" not in st.session_state:
    st.session_state.selected_images = []
if "search_query" not in st.session_state:
    st.session_state.search_query = ""
if "expanded_query" not in st.session_state:
    st.session_state.expanded_query = ""

# -------------------------
# Search Query
# -------------------------
st.markdown("### 🔍 Enter Your Search Query")
search_query = st.text_input(
    "Short phrase (e.g., 'rolled sleeves', 'white tshirt', 'ocean with boat'):",
    placeholder="Type your search query here..."
)

col1, col2 = st.columns([3, 1])
with col1:
    run_search = st.button("🚀 Run Search", type="primary", use_container_width=True)
with col2:
    preview_expansion = st.button("👁️ Preview Expansion", use_container_width=True)

# Preview expansion without running search
if preview_expansion and search_query:
    with st.spinner("Expanding your query..."):
        expanded = expand_query_with_cache(search_query, api_key)
        st.markdown("#### 📝 Expanded Query:")
        st.markdown(f'<div class="expanded-query">{expanded}</div>', unsafe_allow_html=True)

# Run the actual search
if run_search and search_query:
    if not os.path.exists(input_folder):
        st.error(f"Input folder '{input_folder}' not found")
        st.stop()
    
    all_images = [f for f in Path(input_folder).iterdir() if f.is_file() and is_image_file(f.name)]
    if not all_images:
        st.warning("No images found in folder.")
        st.stop()
    
    # Expand the query first
    with st.spinner("🔄 Expanding your query for better search accuracy..."):
        expanded_query = expand_query_with_cache(search_query, api_key)
        st.session_state.expanded_query = expanded_query
    
    # Show the expanded query
    st.markdown("#### 📝 Search Using Expanded Description:")
    st.markdown(f'<div class="expanded-query">{expanded_query}</div>', unsafe_allow_html=True)
    
    st.info(f"Found {len(all_images)} images. Running AI analysis...")

    detected_images = []
    progress_bar = st.progress(0)
    status_text = st.empty()

    for i, img_path in enumerate(all_images):
        status_text.text(f"Analyzing: {img_path.name} ({i+1}/{len(all_images)})")
        is_match, explanation = analyze_image(img_path, client, expanded_query)
        if is_match:
            detected_images.append((img_path, explanation))
        progress_bar.progress((i + 1) / len(all_images))

    status_text.empty()
    st.success(f"✅ Analysis complete! {len(detected_images)} images matched your query.")
    
    # Store results in session state
    st.session_state.detected_images = detected_images
    st.session_state.selected_images = []  # Reset selection
    st.session_state.search_query = search_query

# -------------------------
# Display images with clickable selection
# -------------------------
if st.session_state.detected_images:
    st.markdown("---")
    
    # Show the expanded query used for this search
    if st.session_state.expanded_query:
        with st.expander("📋 View Expanded Query Used", expanded=False):
            st.markdown(f'<div class="expanded-query">{st.session_state.expanded_query}</div>', unsafe_allow_html=True)
    
    # Save button at the top (only enabled when images are selected)
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if len(st.session_state.selected_images) > 0:
            if st.button(f"💾 Save {len(st.session_state.selected_images)} Selected Image(s)", type="primary", use_container_width=True):
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                folder_name = f"{st.session_state.search_query.replace(' ','_')}_{timestamp}"
                save_path = Path(output_base) / folder_name
                os.makedirs(save_path, exist_ok=True)
                
                for img_path in st.session_state.selected_images:
                    shutil.copy(img_path, save_path)
                
                st.success(f"✅ Successfully saved {len(st.session_state.selected_images)} image(s) to: {save_path}")
                st.balloons()
        else:
            st.button(f"💾 Save Selected Images", disabled=True, use_container_width=True)
            st.caption("Select at least one image to enable save")
    
    st.markdown("### 🖼️ Click on images to select/deselect")
    st.caption(f"Selected: {len(st.session_state.selected_images)} / {len(st.session_state.detected_images)}")
    
    # Display images in grid
    cols = st.columns(5)
    for i, (img_path, explanation) in enumerate(st.session_state.detected_images):
        with cols[i % 5]:
            is_selected = img_path in st.session_state.selected_images
            
            # Create clickable image with selection state
            if st.button(
                f"{'✅ ' if is_selected else '⬜ '}{Path(img_path).name}",
                key=f"imgbtn_{i}",
                use_container_width=True
            ):
                if is_selected:
                    st.session_state.selected_images.remove(img_path)
                else:
                    st.session_state.selected_images.append(img_path)
                st.rerun()
            
            # Display image with border based on selection
            if is_selected:
                st.markdown('<div class="image-container image-selected">', unsafe_allow_html=True)
            else:
                st.markdown('<div class="image-container image-unselected">', unsafe_allow_html=True)
            
            st.image(str(img_path), use_container_width=True)
            st.markdown('</div>', unsafe_allow_html=True)
            
            # Show explanation in expander
            with st.expander("🤖 AI Analysis"):
                st.caption(explanation)