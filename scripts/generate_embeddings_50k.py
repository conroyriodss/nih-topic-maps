#!/usr/bin/env python3
"""
Generate PubMedBERT embeddings for 50k sample
Uses same model as 25k for consistency
"""
import pandas as pd
import numpy as np
from transformers import AutoTokenizer, AutoModel
import torch
from tqdm import tqdm
import time

print("=" * 80)
print("GENERATING EMBEDDINGS FOR 50K SAMPLE")
print("=" * 80)

# Load sample
print("\n[1/5] Loading 50k sample...")
df = pd.read_parquet('sample_50k_stratified.parquet')
print(f"  Loaded {len(df):,} grants")

# Prepare text
print("\n[2/5] Preparing text...")
df['text'] = df['PROJECT_TITLE'].fillna('').astype(str)
print(f"  Text prepared for {len(df):,} grants")

# Load model
print("\n[3/5] Loading PubMedBERT model...")
model_name = "microsoft/BiomedNLP-BiomedBERT-base-uncased-abstract-fulltext"
tokenizer = AutoTokenizer.from_pretrained(model_name)
model = AutoModel.from_pretrained(model_name)
model.eval()

device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
model = model.to(device)
print(f"  Model loaded on: {device}")

# Generate embeddings in batches
print("\n[4/5] Generating embeddings...")
print("  This will take 10-15 minutes...")

batch_size = 32
embeddings = []

start_time = time.time()

with torch.no_grad():
    for i in tqdm(range(0, len(df), batch_size), desc="Processing batches"):
        batch_texts = df['text'].iloc[i:i+batch_size].tolist()
        
        # Tokenize
        inputs = tokenizer(
            batch_texts,
            padding=True,
            truncation=True,
            max_length=128,
            return_tensors="pt"
        )
        inputs = {k: v.to(device) for k, v in inputs.items()}
        
        # Generate embeddings
        outputs = model(**inputs)
        batch_embeddings = outputs.last_hidden_state[:, 0, :].cpu().numpy()
        embeddings.append(batch_embeddings)
        
        # Clear cache periodically
        if i % 500 == 0:
            torch.cuda.empty_cache()

embeddings = np.vstack(embeddings)

elapsed = time.time() - start_time
print(f"\n  Embeddings generated in {elapsed/60:.1f} minutes")
print(f"  Shape: {embeddings.shape}")
print(f"  Size: {embeddings.nbytes / 1e9:.2f} GB")

# Save
print("\n[5/5] Saving embeddings...")
df['embedding'] = list(embeddings)
df.to_parquet('embeddings_50k_sample.parquet', index=False)
print(f"  Saved: embeddings_50k_sample.parquet")

print("\n" + "=" * 80)
print("EMBEDDINGS COMPLETE")
print("=" * 80)
print(f"\nNext: Apply hierarchical clustering to 50k grants")
print("=" * 80)
