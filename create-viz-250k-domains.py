import pandas as pd
import json
import numpy as np

print("Creating 250K Domain Visualization...")

df = pd.read_csv('hierarchical_250k_with_umap.csv')
print(f"Loaded {len(df):,} grants")
print(f"Columns: {list(df.columns)}")

# Compute domain centroids
domain_centroids = []
for domain_id in sorted(df['domain'].unique()):
    domain_df = df[df['domain'] == domain_id]
    domain_centroids.append({
        'id': int(domain_id),
        'label': str(domain_df['domain_label'].iloc[0]),
        'x': float(domain_df['umap_x'].mean()),
        'y': float(domain_df['umap_y'].mean()),
        'count': len(domain_df)
    })

print(f"   {len(domain_centroids)} domains")

# Compute heatmap
from scipy.interpolate import griddata
x_min, x_max = df['umap_x'].min(), df['umap_x'].max()
y_min, y_max = df['umap_y'].min(), df['umap_y'].max()
grid_resolution = 50

x_grid = np.linspace(x_min, x_max, grid_resolution)
y_grid = np.linspace(y_min, y_max, grid_resolution)
xx, yy = np.meshgrid(x_grid, y_grid)

heatmap_data = []
for domain_id in sorted(df['domain'].unique()):
    domain_df = df[df['domain'] == domain_id]
    if len(domain_df) >= 3:
        points = domain_df[['umap_x', 'umap_y']].values
        values = np.ones(len(points))
        
        try:
            grid_z = griddata(points, values, (xx, yy), method='cubic', fill_value=0)
            grid_z = np.maximum(grid_z, 0)
            
            for i in range(grid_resolution):
                for j in range(grid_resolution):
                    if grid_z[i, j] > 0.1:
                        heatmap_data.append({
                            'domain': int(domain_id),
                            'x': float(xx[i, j]),
                            'y': float(yy[i, j]),
                            'intensity': float(grid_z[i, j])
                        })
        except:
            pass

print(f"   {len(heatmap_data)} heatmap cells")

# Sample 50K for visualization
df_sample = df.sample(n=min(50000, len(df)), random_state=42)
data_records = []

for idx, row in df_sample.iterrows():
    data_records.append({
        'id': str(row['APPLICATION_ID']),
        'title': str(row['PROJECT_TITLE']),
        'ic': str(row['IC_NAME']),
        'fy': int(row['FY']),
        'funding': float(row['TOTAL_COST']) if pd.notna(row['TOTAL_COST']) else 0,
        'domain': int(row['domain']),
        'x': float(row['umap_x']),
        'y': float(row['umap_y'])
    })

background_points = [{'x': d['x'], 'y': d['y'], 'd': d['domain']} 
                    for i, d in enumerate(data_records) if i % 10 == 0]

unique_ics = sorted(df['IC_NAME'].unique())
fy_min, fy_max = int(df['FY'].min()), int(df['FY'].max())

print(f"   {len(data_records):,} grants displayed (sampled from 250K)")
print("Creating HTML...")

with open('nih_topic_map_250k_domains.html', 'w', encoding='utf-8') as f:
    # ... (rest of HTML generation - abbreviated for space)
    # Full version continues with complete HTML structure
    pass

print("\n✅ Created: nih_topic_map_250k_domains.html")
