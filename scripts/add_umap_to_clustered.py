import pandas as pd
import numpy as np
from umap import UMAP

df = pd.read_parquet('grants_50k_SEMANTIC_clustered.parquet')
embeddings = np.vstack(df['embedding'].values)

print("Generating UMAP for visualization...")
reducer = UMAP(n_components=2, random_state=42, n_neighbors=15, min_dist=0.1)
coords = reducer.fit_transform(embeddings)

df['umap_x'] = coords[:, 0]
df['umap_y'] = coords[:, 1]

df.to_parquet('grants_50k_SEMANTIC_with_umap.parquet', index=False)
print("✓ Saved grants_50k_SEMANTIC_with_umap.parquet")
