#!/usr/bin/env python3
"""
Generate PubMedBERT embeddings for 100k stratified sample
Uses PROJECT_TERMS (auto-detected from schema)
"""
import pandas as pd
import numpy as np
from transformers import AutoTokenizer, AutoModel
import torch
from tqdm import tqdm

print("=" * 70)
print("GENERATING 100K PUBMEDBERT EMBEDDINGS")
print("=" * 70)

# Load 100k sample
sample_file = 'grants_100k_stratified.parquet'
print(f"\n[1/4] Loading {sample_file}...")
df = pd.read_parquet(sample_file)
print(f"  Loaded {len(df):,} grants")

# Identify text column
text_cols = ['PROJECT_TERMS', 'PROJECT_TITLE', 'ABSTRACT_TEXT']
text_col = next((c for c in text_cols if c in df.columns), None)

if not text_col:
    print("✗ No text column found!")
    import sys
    sys.exit(1)

print(f"  Using column: {text_col}")

# Load model
print("\n[2/4] Loading PubMedBERT model...")
model_name = "microsoft/BiomedNLP-PubMedBERT-base-uncased-abstract"
tokenizer = AutoTokenizer.from_pretrained(model_name)
model = AutoModel.from_pretrained(model_name)

device = 'cuda' if torch.cuda.is_available() else 'cpu'
print(f"  Device: {device}")
model = model.to(device)
model.eval()

# Generate embeddings in batches
print(f"\n[3/4] Generating embeddings from {text_col}...")
print("  This will take 30-60 minutes...")

embeddings = []
batch_size = 32
total_batches = (len(df) + batch_size - 1) // batch_size

with tqdm(total=len(df), desc="Embedding") as pbar:
    for i in range(0, len(df), batch_size):
        batch = df[text_col].iloc[i:i+batch_size].fillna('').tolist()
        
        # Tokenize
        inputs = tokenizer(
            batch,
            padding=True,
            truncation=True,
            max_length=512,
            return_tensors='pt'
        )
        inputs = {k: v.to(device) for k, v in inputs.items()}
        
        # Generate embeddings
        with torch.no_grad():
            outputs = model(**inputs)
            batch_embeddings = outputs.last_hidden_state[:, 0, :].cpu().numpy()
        
        embeddings.append(batch_embeddings)
        pbar.update(len(batch))
        
        # Progress update
        if (i // batch_size + 1) % 100 == 0:
            print(f"    Processed {i + len(batch):,}/{len(df):,} ({(i + len(batch))/len(df)*100:.1f}%)")

embeddings = np.vstack(embeddings)
print(f"\n  Generated {embeddings.shape[0]:,} embeddings of {embeddings.shape[1]}D")

# Save
print("\n[4/4] Saving...")
df_embeddings = pd.DataFrame({
    'APPLICATION_ID': df['APPLICATION_ID'],
    'embedding': [emb.tolist() for emb in embeddings]
})

output_file = 'embeddings_100k_pubmedbert.parquet'
df_embeddings.to_parquet(output_file, index=False)
print(f"  ✓ {output_file}")

# Verify
file_size = pd.read_parquet(output_file).memory_usage(deep=True).sum() / 1024**2
print(f"  Size: {file_size:.1f} MB")

print("\n" + "=" * 70)
print("EMBEDDINGS COMPLETE!")
print("=" * 70)
print(f"\nNext: python3 cluster_100k_efficient.py")
