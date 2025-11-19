import os
import shutil
import random
import json
import time
from pathlib import Path
from datetime import datetime
import streamlit as st
from PIL import Image
from google import genai
from google.genai import types

# Import the query expander
from scripts.query_expander import expand_query_with_cache

# -------------------------
# CONFIG  /Users/jay/Desktop/miss-you-india /Users/jay/Downloads/fall-2025
# -------------------------
MODEL_NAME = "gemini-2.0-flash-exp"
MAX_RETRIES_PER_KEY = 2  # Retries before switching API key
ROTATION_INTERVAL = 10  # Rotate key every N images as preventive measure

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
    .api-key-info {
        background-color: #fff3cd;
        padding: 10px;
        border-radius: 5px;
        border-left: 3px solid #ffc107;
        margin: 10px 0;
        font-size: 0.9em;
    }
</style>
""", unsafe_allow_html=True)

# -------------------------
# API KEY MANAGEMENT
# -------------------------
class APIKeyManager:
    def __init__(self):
        self.creds_file = Path(__file__).parent / "creds.json"
        self.all_keys = []
        self.current_key_index = 0
        self.used_keys = set()
        self.load_keys()
    
    def load_keys(self):
        """Load all API keys from creds.json"""
        if not self.creds_file.exists():
            raise FileNotFoundError("creds.json not found in script directory.")
        
        try:
            with open(self.creds_file, 'r') as f:
                creds = json.load(f)
            self.all_keys = creds.get("api_keys", [])
            if not self.all_keys:
                raise ValueError("No API keys found in creds.json")
            random.shuffle(self.all_keys)  # Randomize order
        except Exception as e:
            raise Exception(f"Error reading creds.json: {e}")
    
    def get_random_key(self):
        """Get a random API key that hasn't been used recently"""
        if len(self.used_keys) >= len(self.all_keys):
            # All keys have been used, reset
            self.used_keys.clear()
        
        available_keys = [k for k in self.all_keys if k not in self.used_keys]
        if not available_keys:
            available_keys = self.all_keys
        
        key = random.choice(available_keys)
        self.used_keys.add(key)
        return key
    
    def get_next_key(self):
        """Get next API key in rotation"""
        self.current_key_index = (self.current_key_index + 1) % len(self.all_keys)
        return self.all_keys[self.current_key_index]
    
    def get_key_count(self):
        """Return total number of available keys"""
        return len(self.all_keys)

# -------------------------
# HELPER FUNCTIONS
# -------------------------
def get_mime_type(image_path):
    ext = Path(image_path).suffix.lower()
    return {
        '.jpg':'image/jpeg', '.jpeg':'image/jpeg', '.png':'image/png', 
        '.webp':'image/webp', '.gif':'image/gif', '.bmp':'image/bmp', 
        '.heic':'image/heic'
    }.get(ext, 'image/jpeg')

def is_image_file(filename):
    return Path(filename).suffix.lower() in {'.jpg', '.jpeg', '.png', '.webp', '.gif', '.bmp', '.heic'}

def is_rate_limit_error(error_msg):
    """Check if error is due to rate limiting"""
    rate_limit_indicators = [
        'rate limit',
        'quota',
        'too many requests',
        '429',
        'resource exhausted',
        'limit exceeded'
    ]
    error_str = str(error_msg).lower()
    return any(indicator in error_str for indicator in rate_limit_indicators)

def analyze_image_with_retry(image_path, api_key_manager, expanded_query, status_placeholder=None):
    """
    Analyze image with automatic API key rotation on rate limit errors.
    Returns: (is_match, explanation, api_key_used)
    """
    max_attempts = min(3, api_key_manager.get_key_count())  # Try up to 3 different keys
    
    for attempt in range(max_attempts):
        try:
            # Get a fresh API key for this attempt
            if attempt == 0:
                api_key = api_key_manager.get_random_key()
            else:
                api_key = api_key_manager.get_next_key()
                if status_placeholder:
                    status_placeholder.warning(f"⚠️ Switching to different API key (attempt {attempt + 1}/{max_attempts})")
                time.sleep(1)  # Brief pause before retry
            
            client = genai.Client(api_key=api_key)
            
            # Analyze the image
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
            
            return is_match, text, api_key
        
        except Exception as e:
            error_msg = str(e)
            
            if is_rate_limit_error(error_msg):
                if attempt < max_attempts - 1:
                    if status_placeholder:
                        status_placeholder.warning(f"🔄 Rate limit hit, switching API key...")
                    continue
                else:
                    return False, f"Rate limit error after trying {max_attempts} keys: {error_msg}", None
            else:
                # Non-rate-limit error, return immediately
                return False, f"Error: {error_msg}", None
    
    return False, "Failed after all retry attempts", None

# -------------------------
# STREAMLIT UI
# -------------------------
st.set_page_config(page_title="AI Image Search & Selection", layout="wide")
st.title("🖼️ AI Image Search & Selection")
st.write("""
Search images using natural language. Your query will be automatically expanded into a detailed description for better accuracy.
""")

# Initialize API Key Manager
try:
    if 'api_key_manager' not in st.session_state:
        st.session_state.api_key_manager = APIKeyManager()
    api_key_manager = st.session_state.api_key_manager
except Exception as e:
    st.error(f"Failed to initialize API keys: {e}")
    st.stop()

# Sidebar: input/output folders
input_folder = st.sidebar.text_input("Input Folder Path", value="./images")
output_base = st.sidebar.text_input("Output Base Folder", value="./selected_images")

st.sidebar.markdown("### API Key Info")
st.sidebar.info(f"🔑 {api_key_manager.get_key_count()} API keys loaded from creds.json")
st.sidebar.caption("Keys will automatically rotate to avoid rate limits")

# Manual API key override (optional)
manual_key = st.sidebar.text_input("Override with manual API key (optional)", type="password")
if manual_key:
    st.sidebar.warning("⚠️ Using manual key - auto-rotation disabled")

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
        preview_key = manual_key if manual_key else api_key_manager.get_random_key()
        expanded = expand_query_with_cache(search_query, preview_key)
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
        expand_key = manual_key if manual_key else api_key_manager.get_random_key()
        expanded_query = expand_query_with_cache(search_query, expand_key)
        st.session_state.expanded_query = expanded_query
    
    # Show the expanded query
    st.markdown("#### 📝 Search Using Expanded Description:")
    st.markdown(f'<div class="expanded-query">{expanded_query}</div>', unsafe_allow_html=True)
    
    st.info(f"Found {len(all_images)} images. Running AI analysis with automatic key rotation...")

    detected_images = []
    progress_bar = st.progress(0)
    status_text = st.empty()
    key_rotation_info = st.empty()

    images_processed_with_current_key = 0
    
    for i, img_path in enumerate(all_images):
        # Rotate key preventively every N images
        if not manual_key and images_processed_with_current_key >= ROTATION_INTERVAL:
            key_rotation_info.markdown(
                f'<div class="api-key-info">🔄 Preventively rotating API key after {ROTATION_INTERVAL} images</div>', 
                unsafe_allow_html=True
            )
            images_processed_with_current_key = 0
            time.sleep(0.5)
            key_rotation_info.empty()
        
        status_text.text(f"Analyzing: {img_path.name} ({i+1}/{len(all_images)})")
        
        if manual_key:
            # Use manual key without rotation
            client = genai.Client(api_key=manual_key)
            from io import BytesIO
            with Image.open(img_path) as img:
                img_rgb = img.convert("RGB")
                buf = BytesIO()
                img_rgb.save(buf, format='JPEG')
                image_bytes = buf.getvalue()
            mime_type = get_mime_type(img_path)
            image_part = types.Part.from_bytes(data=image_bytes, mime_type=mime_type)
            prompt = f"""Analyze this image carefully and determine if it matches the following description:
"{expanded_query}"
Important instructions:
- Focus on the main subject of the image
- Ignore irrelevant background details
- Consider all the criteria mentioned in the description
- Answer ONLY "Yes" or "No", followed by a brief explanation of why it matches or doesn't match"""
            try:
                response = client.models.generate_content(model=MODEL_NAME, contents=[prompt, image_part])
                text = response.text.strip()
                is_match = text.lower().startswith("yes")
            except Exception as e:
                is_match, text = False, str(e)
        else:
            # Use automatic key rotation
            is_match, text, key_used = analyze_image_with_retry(
                img_path, api_key_manager, expanded_query, status_text
            )
            images_processed_with_current_key += 1
        
        if is_match:
            detected_images.append((img_path, text))
        
        progress_bar.progress((i + 1) / len(all_images))

    status_text.empty()
    key_rotation_info.empty()
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