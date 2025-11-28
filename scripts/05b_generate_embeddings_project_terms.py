#!/usr/bin/env python3
"""
Generate embeddings using PubMedBERT for PROJECT_TERMS only
This uses NIH's curated terminology rather than full abstract text.
Project: od-cl-odss-conroyri-f75a
Model: microsoft/BiomedNLP-PubMedBERT-base-uncased-abstract-fulltext
"""

from google.cloud import bigquery
import pandas as pd
import numpy as np
import time
from datetime import datetime
import json
import torch
from transformers import AutoTokenizer, AutoModel
from tqdm import tqdm
import os

PROJECT_ID = "od-cl-odss-conroyri-f75a"
DATASET_ID = "nih_data"

# Check for GPU
device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
print(f"\nUsing device: {device}")
if device.type == 'cpu':
    print("⚠ No GPU detected. This will take 2-4 hours on CPU.")
    print("  Consider using a GPU-enabled VM for faster processing.")
else:
    print(f"✓ GPU detected: {torch.cuda.get_device_name(0)}")
    print("  Estimated time: 15-30 minutes")

bq_client = bigquery.Client(project=PROJECT_ID)

print("\n" + "#"*70)
print("# PubMedBERT Embeddings - PROJECT_TERMS Only")
print(f"# Project: {PROJECT_ID}")
print(f"# Model: microsoft/BiomedNLP-PubMedBERT-base-uncased-abstract-fulltext")
print(f"# Embedding dimension: 768")
print(f"# Text source: PROJECT_TERMS (curated NIH terminology)")
print("#"*70 + "\n")

start_time = time.time()

# Load sample data with PROJECT_TERMS
print("Loading 50K sample with PROJECT_TERMS from BigQuery...")
query = f"""
SELECT 
    p.APPLICATION_ID,
    p.FISCAL_YEAR,
    p.IC_NAME,
    p.TOTAL_COST,
    p.PROJECT_TITLE,
    proj.PROJECT_TERMS
FROM `{PROJECT_ID}.{DATASET_ID}.grant_text_sample` p
LEFT JOIN `{PROJECT_ID}.{DATASET_ID}.projects_all` proj
    ON p.APPLICATION_ID = proj.APPLICATION_ID
WHERE proj.PROJECT_TERMS IS NOT NULL
    AND LENGTH(proj.PROJECT_TERMS) > 10
ORDER BY p.FISCAL_YEAR, p.APPLICATION_ID
"""

df = bq_client.query(query).to_dataframe()
print(f"✓ Loaded {len(df):,} grants with PROJECT_TERMS")
print(f"  Avg PROJECT_TERMS length: {df['PROJECT_TERMS'].str.len().mean():.0f} chars\n")

# Check for missing data
if len(df) == 0:
    print("❌ ERROR: No grants with PROJECT_TERMS found!")
    print("   Check if projects_all table has PROJECT_TERMS column.")
    exit(1)

# Sample PROJECT_TERMS examples
print("Sample PROJECT_TERMS (first 3 grants):")
for idx, terms in enumerate(df['PROJECT_TERMS'].head(3)):
    print(f"  {idx+1}. {terms[:200]}...")
print()

# Load PubMedBERT model
print("Loading PubMedBERT model...")
model_name = "microsoft/BiomedNLP-PubMedBERT-base-uncased-abstract-fulltext"
tokenizer = AutoTokenizer.from_pretrained(model_name)
model = AutoModel.from_pretrained(model_name)
model.to(device)
model.eval()
print("✓ Model loaded\n")

# Generate embeddings
print("Generating embeddings from PROJECT_TERMS...")
print(f"Batch processing {len(df):,} grants\n")

BATCH_SIZE = 32 if device.type == 'cuda' else 8
MAX_LENGTH = 512  # PubMedBERT max sequence length

embeddings_list = []

with torch.no_grad():
    for i in tqdm(range(0, len(df), BATCH_SIZE), desc="Processing"):
        batch_end = min(i + BATCH_SIZE, len(df))
        batch = df.iloc[i:batch_end]
        
        # Use PROJECT_TERMS instead of combined_text
        texts = []
        for _, row in batch.iterrows():
            # Use PROJECT_TERMS directly (already curated and concise)
            text = str(row['PROJECT_TERMS'])
            texts.append(text)
        
        try:
            # Tokenize
            inputs = tokenizer(
                texts,
                padding=True,
                truncation=True,
                max_length=MAX_LENGTH,
                return_tensors='pt'
            ).to(device)
            
            # Get embeddings
            outputs = model(**inputs)
            
            # Use [CLS] token embedding (first token)
            embeddings = outputs.last_hidden_state[:, 0, :].cpu().numpy()
            
            # Store results
            for j, embedding in enumerate(embeddings):
                idx = i + j
                embeddings_list.append({
                    'APPLICATION_ID': df.iloc[idx]['APPLICATION_ID'],
                    'FISCAL_YEAR': int(df.iloc[idx]['FISCAL_YEAR']),
                    'IC_NAME': df.iloc[idx]['IC_NAME'],
                    'TOTAL_COST': float(df.iloc[idx]['TOTAL_COST']) if pd.notna(df.iloc[idx]['TOTAL_COST']) else 0.0,
                    'PROJECT_TITLE': df.iloc[idx]['PROJECT_TITLE'],
                    'PROJECT_TERMS': df.iloc[idx]['PROJECT_TERMS'],
                    'embedding': embedding.tolist()
                })
        
        except Exception as e:
            print(f"\nError at batch {i}: {e}")
            # Add zero vectors for failed batch
            for j in range(len(batch)):
                idx = i + j
                embeddings_list.append({
                    'APPLICATION_ID': df.iloc[idx]['APPLICATION_ID'],
                    'FISCAL_YEAR': int(df.iloc[idx]['FISCAL_YEAR']),
                    'IC_NAME': df.iloc[idx]['IC_NAME'],
                    'TOTAL_COST': float(df.iloc[idx]['TOTAL_COST']) if pd.notna(df.iloc[idx]['TOTAL_COST']) else 0.0,
                    'PROJECT_TITLE': df.iloc[idx]['PROJECT_TITLE'],
                    'PROJECT_TERMS': df.iloc[idx]['PROJECT_TERMS'],
                    'embedding': [0.0] * 768
                })
            continue

elapsed = time.time() - start_time
print(f"\n✓ Generated {len(embeddings_list):,} embeddings in {elapsed/60:.1f} minutes")

# Save results
print("\nSaving embeddings...")
os.makedirs('data/processed', exist_ok=True)
embeddings_df = pd.DataFrame(embeddings_list)

# Save as Parquet
local_file = 'data/processed/embeddings_project_terms_50k.parquet'
embeddings_df.to_parquet(local_file, compression='snappy')
print(f"✓ Saved to {local_file}")
print(f"  File size: {os.path.getsize(local_file) / 1024 / 1024:.1f} MB")

# Upload to Cloud Storage
print("\nUploading to Cloud Storage...")
import subprocess
subprocess.run([
    'gsutil', 'cp', local_file,
    'gs://od-cl-odss-conroyri-nih-embeddings/sample/'
], check=True)
print(f"✓ Uploaded to gs://od-cl-odss-conroyri-nih-embeddings/sample/")

# Create manifest
manifest = {
    'project_id': PROJECT_ID,
    'sample_size': len(embeddings_df),
    'embedding_dim': 768,
    'model': 'microsoft/BiomedNLP-PubMedBERT-base-uncased-abstract-fulltext',
    'text_source': 'PROJECT_TERMS',
    'device': str(device),
    'time_minutes': elapsed / 60,
    'avg_terms_length': float(df['PROJECT_TERMS'].str.len().mean()),
    'timestamp': datetime.now().isoformat()
}

with open('data/processed/embeddings_manifest_project_terms.json', 'w') as f:
    json.dump(manifest, f, indent=2)

subprocess.run([
    'gsutil', 'cp', 'data/processed/embeddings_manifest_project_terms.json',
    'gs://od-cl-odss-conroyri-nih-embeddings/sample/'
], check=True)

print("\n" + "="*70)
print("EMBEDDINGS GENERATION COMPLETE")
print("="*70)
print(f"Total time: {elapsed/60:.1f} minutes")
print(f"Embeddings: {len(embeddings_df):,}")
print(f"Model: PubMedBERT")
print(f"Text source: PROJECT_TERMS (curated NIH terminology)")
print(f"Device: {device}")
print(f"\nNext steps:")
print(f"1. Check K optimization results:")
print(f"   python3 scripts/check_k_results.py")
print(f"\n2. Or cluster with K=150:")
print(f"   python3 scripts/06_cluster_project_terms.py --k 150")
