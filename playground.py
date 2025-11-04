import os
from PIL import Image
from tqdm import tqdm
import torch
from sentence_transformers import SentenceTransformer, util

# Optional: allow Pillow to open HEIC files (iPhone photos)
try:
    from pillow_heif import register_heif_opener
    register_heif_opener()
except ImportError:
    print("Tip: install pillow-heif to support .HEIC images")

# ---------------- CONFIG ----------------
image_folder = "/Users/jay/Downloads/fall-2025"  # <-- change this
model_name = "clip-ViT-B-32"          # can also try "clip-ViT-L-14"
top_k = 10
# ----------------------------------------

# Load CLIP model
print(f"Loading model: {model_name}")
model = SentenceTransformer(model_name)

# Collect image paths
image_paths = [
    os.path.join(image_folder, f)
    for f in os.listdir(image_folder)
    if f.lower().endswith((".jpg", ".jpeg", ".png", ".heic"))
]
print(f"Found {len(image_paths)} images")

# Load and encode images
images, valid_paths = [], []
for p in tqdm(image_paths, desc="Loading images"):
    try:
        img = Image.open(p).convert("RGB")
        images.append(img)
        valid_paths.append(p)
    except Exception as e:
        print(f"Skipping {p}: {e}")

print(f"Encoding {len(valid_paths)} valid images ...")
image_embs = model.encode(
    images,
    batch_size=16,
    convert_to_tensor=True,
    show_progress_bar=True
)

# Normalize embeddings for cosine similarity
image_embs = image_embs / image_embs.norm(dim=1, keepdim=True)

# Search function
def search_images(query, top_k=top_k):
    query_emb = model.encode(query, convert_to_tensor=True)
    query_emb = query_emb / query_emb.norm()
    cos_scores = util.cos_sim(query_emb, image_embs)[0]
    top_results = torch.topk(cos_scores, k=top_k)

    print(f"\nTop {top_k} results for '{query}':")
    for score, idx in zip(top_results.values, top_results.indices):
        print(f"{valid_paths[idx]}  (score={score:.4f})")

# -------------------------------------------------
# Example interactive queries
# -------------------------------------------------
while True:
    q = input("\nEnter search query (or 'q' to quit): ").strip()
    if q.lower() in {"q", "quit", "exit"}:
        break
    search_images(q)
