import os
from PIL import Image
import torch
import streamlit as st
from sentence_transformers import SentenceTransformer, util
from tqdm import tqdm
from pillow_heif import register_heif_opener
register_heif_opener()

# -------------------------
# CONFIG
# -------------------------
IMAGE_FOLDER = "/Users/jay/Downloads/fall-2025"  # <-- change this
MODEL_NAME = "clip-ViT-B-32"

# -------------------------
# STREAMLIT PAGE SETUP
# -------------------------
st.set_page_config(page_title="Local AI Image Search", layout="wide")
st.title("🔍 Local AI Image Search")
st.write("Search your local images using natural language (text query). Fully offline.")

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

    # Encode all images
    image_embs = _model.encode(images, batch_size=16, convert_to_tensor=True, show_progress_bar=True)
    image_embs = image_embs / image_embs.norm(dim=1, keepdim=True)  # normalize
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

if query:
    # Encode query
    query_emb = model.encode(query, convert_to_tensor=True)
    query_emb = query_emb / query_emb.norm()

    # Cosine similarity
    cos_scores = util.cos_sim(query_emb, image_embs)[0]
    top_results = torch.topk(cos_scores, k=min(top_k, len(image_paths)))

    st.markdown(f"### Top {top_k} results for '{query}'")
    cols = st.columns(5)
    for i, idx in enumerate(top_results.indices):
        with cols[i % 5]:
            st.image(image_paths[idx], caption=os.path.basename(image_paths[idx]), use_container_width=True)
