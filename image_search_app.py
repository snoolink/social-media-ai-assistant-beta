import os
from PIL import Image
import torch
import streamlit as st
from sentence_transformers import SentenceTransformer, util
from tqdm import tqdm
from datetime import datetime
import shutil

# -------------------------
# CONFIG
# -------------------------
IMAGE_FOLDER = "/Users/jay/Documents/Photarah/Photos"  # <-- change this
# MODEL_NAME = "clip-ViT-L-14"
MODEL_NAME = "openai/clip-vit-large-patch14"


# Optional: HEIC support
try:
    from pillow_heif import register_heif_opener
    register_heif_opener()
except ImportError:
    st.warning("Tip: install pillow-heif to support .HEIC images")

# -------------------------
# STREAMLIT PAGE SETUP
# -------------------------
st.set_page_config(page_title="Local AI Image Search", layout="wide")
st.title("🔍 Local AI Image Search with Select & Copy")
st.write("Search your local images using natural language, select images, and save them to a new folder.")

# -------------------------
# LOAD MODEL
# -------------------------
@st.cache_resource
def load_model():
    return SentenceTransformer(MODEL_NAME)

model = load_model()

# -------------------------
# LOAD + ENCODE IMAGES
# -------------------------
@st.cache_data(show_spinner="Encoding images...")
def load_and_encode_images(folder, _model):
    image_paths, images = [], []
    for f in os.listdir(folder):
        if f.lower().endswith((".jpg", ".jpeg", ".png", ".heic")):
            path = os.path.join(folder, f)
            try:
                img = Image.open(path).convert("RGB")
                images.append(img)
                image_paths.append(path)
            except Exception as e:
                print(f"Skipping {path}: {e}")
    if not images:
        return [], None
    # Encode images
    image_embs = _model.encode(images, batch_size=16, convert_to_tensor=True, show_progress_bar=True)
    image_embs = image_embs / image_embs.norm(dim=1, keepdim=True)
    return image_paths, image_embs

image_paths, image_embs = load_and_encode_images(IMAGE_FOLDER, model)
if not image_paths:
    st.error("No valid images found in folder.")
    st.stop()

# -------------------------
# SEARCH INTERFACE
# -------------------------
query = st.text_input("Enter search query (e.g., 'black shirt', 'golf photos'):")
top_k = st.slider("Number of results to show", min_value=5, max_value=50, value=10)

selected_images = []

if query:
    # Encode query
    query_emb = model.encode(query, convert_to_tensor=True)
    query_emb = query_emb / query_emb.norm()

    # Cosine similarity
    cos_scores = util.cos_sim(query_emb, image_embs)[0]
    top_results = torch.topk(cos_scores, k=min(top_k, len(image_paths)))

    st.markdown(f"### Top {top_k} results for '{query}'")

    # Display thumbnails with selection checkboxes
    cols = st.columns(5)
    checkboxes = []
    for i, idx in enumerate(top_results.indices):
        with cols[i % 5]:
            st.image(image_paths[idx], caption=os.path.basename(image_paths[idx]), use_container_width=True)
            checkbox = st.checkbox("Select", key=f"select_{idx}")
            if checkbox:
                selected_images.append(image_paths[idx])

# -------------------------
# COPY SELECTED IMAGES
# -------------------------
if selected_images:
    if st.button("Save Selected Images"):
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        folder_name = f"{query.replace(' ', '_')}_{timestamp}"
        save_path = os.path.join(os.getcwd(), folder_name)
        os.makedirs(save_path, exist_ok=True)

        for img_path in selected_images:
            shutil.copy(img_path, save_path)

        st.success(f"{len(selected_images)} images saved to folder: {save_path}")
