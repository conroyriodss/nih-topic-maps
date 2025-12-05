#!/usr/bin/env python3
"""
Generate embeddings for 50k sample using Vertex AI text-embedding-005
Much faster than local PubMedBERT and no torch conflicts
"""
import pandas as pd
import numpy as np
from vertexai.language_models import TextEmbeddingModel
import vertexai
from tqdm import tqdm
import time

PROJECT_ID = 'od-cl-odss-conroyri-f75a'
REGION = 'us-central1'

print("=" * 80)
print("GENERATING EMBEDDINGS FOR 50K SAMPLE (VERTEX AI)")
print("=" * 80)

# Initialize Vertex AI
print("\n[1/5] Initializing Vertex AI...")
vertexai.init(project=PROJECT_ID, location=REGION)
model = TextEmbeddingModel.from_pretrained("text-embedding-005")
print("  Model: text-embedding-005 (768-dim, same as PubMedBERT)")

# Load sample
print("\n[2/5] Loading 50k sample...")
df = pd.read_parquet('sample_50k_stratified.parquet')
print(f"  Loaded {len(df):,} grants")

# Prepare text
print("\n[3/5] Preparing text...")
df['text'] = df['PROJECT_TITLE'].fillna('').astype(str)
texts = df['text'].tolist()
print(f"  Text prepared for {len(texts):,} grants")

# Generate embeddings in batches
print("\n[4/5] Generating embeddings...")
print("  Using Vertex AI API (batch processing)")
print("  This will take 5-8 minutes...")

batch_size = 250  # Vertex AI supports large batches
embeddings = []

start_time = time.time()

for i in tqdm(range(0, len(texts), batch_size), desc="API batches"):
    batch_texts = texts[i:i+batch_size]
    
    try:
        # Get embeddings from Vertex AI
        batch_embeddings = model.get_embeddings(batch_texts)
        batch_vectors = [emb.values for emb in batch_embeddings]
        embeddings.extend(batch_vectors)
    except Exception as e:
        print(f"\n  Warning: Batch {i//batch_size} failed: {e}")
        print(f"  Retrying with smaller batch...")
        # Retry with smaller batches
        for text in batch_texts:
            try:
                emb = model.get_embeddings([text])[0]
                embeddings.append(emb.values)
            except:
                # Fallback: zero vector
                embeddings.append([0.0] * 768)
        
    # Rate limiting
    if i % 5000 == 0 and i > 0:
        time.sleep(1)

embeddings_array = np.array(embeddings)

elapsed = time.time() - start_time
print(f"\n  Embeddings generated in {elapsed/60:.1f} minutes")
print(f"  Shape: {embeddings_array.shape}")
print(f"  Size: {embeddings_array.nbytes / 1e9:.2f} GB")

# Verify dimensions
if embeddings_array.shape[0] != len(df):
    print(f"\n  ⚠️  Warning: Generated {len(embeddings_array)} embeddings for {len(df)} grants")
    # Pad if needed
    if embeddings_array.shape[0] < len(df):
        missing = len(df) - embeddings_array.shape[0]
        padding = np.zeros((missing, 768))
        embeddings_array = np.vstack([embeddings_array, padding])

# Save
print("\n[5/5] Saving embeddings...")
df['embedding'] = list(embeddings_array)
df.to_parquet('embeddings_50k_sample.parquet', index=False)
print(f"  Saved: embeddings_50k_sample.parquet")

# Quick quality check
print("\n  Quality check:")
non_zero = np.count_nonzero(embeddings_array.sum(axis=1))
print(f"    Non-zero embeddings: {non_zero:,} ({non_zero/len(df)*100:.1f}%)")
print(f"    Mean norm: {np.linalg.norm(embeddings_array, axis=1).mean():.2f}")

print("\n" + "=" * 80)
print("EMBEDDINGS COMPLETE - READY FOR CLUSTERING")
print("=" * 80)
print(f"\nDataset: 50,000 grants")
print(f"Embeddings: 768 dimensions")
print(f"Next: Apply hierarchical clustering")
print("=" * 80)
