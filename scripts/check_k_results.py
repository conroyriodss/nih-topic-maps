#!/usr/bin/env python3
"""Check K optimization results from previous run"""
import pandas as pd
import json
from google.cloud import storage

BUCKET_NAME = "od-cl-odss-conroyri-nih-embeddings"
RESULTS_PATH = "sample/k_optimization_results.json"

print("\n" + "="*70)
print("Checking K Optimization Results")
print("="*70 + "\n")

client = storage.Client()
bucket = client.bucket(BUCKET_NAME)
blob = bucket.blob(RESULTS_PATH)

if blob.exists():
    results_json = blob.download_as_text()
    results = json.loads(results_json)
    print("✓ K optimization results found!\n")
    print(f"Date: {results.get('timestamp', 'Unknown')}")
    print(f"K values tested: {results.get('k_values', 'Unknown')}\n")
    if 'metrics' in results:
        df = pd.DataFrame(results['metrics'])
        print("Clustering Quality Metrics:")
        print(df.to_string(index=False))
        if 'optimal_k' in results:
            print(f"\n✓ Recommended K: {results['optimal_k']}")
        else:
            best_idx = df['silhouette_score'].idxmax()
            optimal_k = df.iloc[best_idx]['k']
            print(f"\n✓ Best K by silhouette score: {optimal_k}")
else:
    print("❌ K optimization results not found")
    print("\nProceed with K=150 (NIH Maps standard)")
