#!/usr/bin/env python3
"""
Generate embeddings using PubMedBERT for 50K sample
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

PROJECT_ID = "od-cl-odss-conroyri-f75a"
DATASET_ID = "nih_data"

# Check for GPU
device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
print(f"\nUsing device: {device}")
if device.type == 'cpu':
    print("⚠ No GPU detected. This will take 6-10 hours on CPU.")
    print("  Consider using a GPU-enabled VM for faster processing.")
else:
    print(f"✓ GPU detected: {torch.cuda.get_device_name(0)}")
    print("  Estimated time: 30-60 minutes")

bq_client = bigquery.Client(project=PROJECT_ID)

print("\n" + "#"*70)
print("# PubMedBERT Embeddings Generation - Sample")
print(f"# Project: {PROJECT_ID}")
print(f"# Model: microsoft/BiomedNLP-PubMedBERT-base-uncased-abstract-fulltext")
print(f"# Embedding dimension: 768")
print("#"*70 + "\n")

start_time = time.time()

# Load sample data
print("Loading 50K sample from BigQuery...")
query = f"""
SELECT 
    APPLICATION_ID,
    combined_text,
    FISCAL_YEAR,
    IC_NAME,
    TOTAL_COST,
    PROJECT_TITLE
FROM `{PROJECT_ID}.{DATASET_ID}.grant_text_sample`
ORDER BY FISCAL_YEAR, APPLICATION_ID
"""

df = bq_client.query(query).to_dataframe()
print(f"✓ Loaded {len(df):,} grants\n")

# Load PubMedBERT model
print("Loading PubMedBERT model...")
model_name = "microsoft/BiomedNLP-PubMedBERT-base-uncased-abstract-fulltext"
tokenizer = AutoTokenizer.from_pretrained(model_name)
model = AutoModel.from_pretrained(model_name)
model.to(device)
model.eval()
print("✓ Model loaded\n")

# Generate embeddings
print("Generating embeddings...")
print(f"Batch processing {len(df):,} grants\n")

BATCH_SIZE = 32 if device.type == 'cuda' else 8  # Larger batches with GPU
MAX_LENGTH = 512  # PubMedBERT max sequence length

embeddings_list = []

with torch.no_grad():
    for i in tqdm(range(0, len(df), BATCH_SIZE), desc="Processing"):
        batch_end = min(i + BATCH_SIZE, len(df))
        batch = df.iloc[i:batch_end]
        
        # Prepare batch texts
        texts = []
        for _, row in batch.iterrows():
            # Truncate to fit model
            text = str(row['combined_text'])[:2000]
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
                    'TOTAL_COST': float(df.iloc[idx]['TOTAL_COST']),
                    'PROJECT_TITLE': df.iloc[idx]['PROJECT_TITLE'],
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
                    'TOTAL_COST': float(df.iloc[idx]['TOTAL_COST']),
                    'PROJECT_TITLE': df.iloc[idx]['PROJECT_TITLE'],
                    'embedding': [0.0] * 768
                })
            continue

elapsed = time.time() - start_time
print(f"\n✓ Generated {len(embeddings_list):,} embeddings in {elapsed/60:.1f} minutes")

# Save results
print("\nSaving embeddings...")
embeddings_df = pd.DataFrame(embeddings_list)

# Save as Parquet
local_file = 'data/processed/embeddings_pubmedbert_50k.parquet'
embeddings_df.to_parquet(local_file, compression='snappy')
print(f"✓ Saved to {local_file}")

# Upload to Cloud Storage
print("Uploading to Cloud Storage...")
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
    'device': str(device),
    'time_minutes': elapsed / 60,
    'timestamp': datetime.now().isoformat()
}

with open('data/processed/embeddings_manifest_pubmedbert.json', 'w') as f:
    json.dump(manifest, f, indent=2)

subprocess.run([
    'gsutil', 'cp', 'data/processed/embeddings_manifest_pubmedbert.json',
    'gs://od-cl-odss-conroyri-nih-embeddings/sample/'
])

print("\n" + "="*70)
print("EMBEDDINGS GENERATION COMPLETE")
print("="*70)
print(f"Total time: {elapsed/60:.1f} minutes")
print(f"Embeddings: {len(embeddings_df):,}")
print(f"Model: PubMedBERT")
print(f"Device: {device}")
print(f"\nNext step: Topic modeling with BERTopic")
print(f"  python3 scripts/06_topic_modeling_sample.py")
