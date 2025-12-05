#!/usr/bin/env python3
"""
Create award map using proper UMAP (matching transaction methodology)
"""
import pandas as pd
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.decomposition import TruncatedSVD
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score
import json

print("="*70)
print("CREATING IMPROVED AWARD MAP WITH PROPER UMAP")
print("="*70)

# Load embeddings
print("\n[1/5] Loading embeddings...")
embeddings = np.load('award_embeddings_tfidf_103k.npy')
df = pd.read_csv('awards_110k_clustered_k75.csv')
print(f"Embeddings: {embeddings.shape}")
print(f"Awards: {len(df):,}")

# Install umap-learn without parametric dependencies
print("\n[2/5] Setting up UMAP...")
import sys
import subprocess
subprocess.check_call([sys.executable, "-m", "pip", "install", 
                      "umap-learn", "--no-deps", "-q"])
subprocess.check_call([sys.executable, "-m", "pip", "install", 
                      "pynndescent", "scikit-learn", "scipy", "numba", "-q"])

from umap import UMAP

print("\n[3/5] Generating UMAP projection (matching transaction parameters)...")
print("   This will take 5-10 minutes...")

umap_model = UMAP(
    n_components=2,
    n_neighbors=50,      # Match transaction map (was 15)
    min_dist=0.0,        # Match transaction map (was 0.1)
    metric='cosine',
    random_state=42,
    verbose=True
)

umap_coords = umap_model.fit_transform(embeddings)
df['umap_x_improved'] = umap_coords[:, 0]
df['umap_y_improved'] = umap_coords[:, 1]

print(f"\n   UMAP complete!")
print(f"   X range: [{df['umap_x_improved'].min():.2f}, {df['umap_x_improved'].max():.2f}]")
print(f"   Y range: [{df['umap_y_improved'].min():.2f}, {df['umap_y_improved'].max():.2f}]")

# Re-cluster in 2D UMAP space (better for visualization)
print("\n[4/5] Clustering in 2D UMAP space...")

kmeans_2d = KMeans(
    n_clusters=75,
    random_state=42,
    n_init=20,
    max_iter=500
)

df['cluster_umap_k75'] = kmeans_2d.fit_predict(umap_coords)

silhouette_2d = silhouette_score(umap_coords, df['cluster_umap_k75'], sample_size=10000)
print(f"   2D clustering silhouette: {silhouette_2d:.4f}")

# Generate cluster labels
print("\n[5/5] Generating cluster labels...")

cluster_info = {}
for cluster_id in sorted(df['cluster_umap_k75'].unique()):
    cluster_df = df[df['cluster_umap_k75'] == cluster_id]
    
    vec = TfidfVectorizer(max_features=5, stop_words='english', ngram_range=(1,2))
    titles = ' '.join(cluster_df['project_title'].head(100).tolist())
    
    try:
        vec.fit([titles])
        keywords = ' & '.join([k.title() for k in vec.get_feature_names_out()[:3]])
    except:
        keywords = f'Cluster {cluster_id}'
    
    cluster_info[str(cluster_id)] = {
        'label': keywords,
        'n_awards': int(len(cluster_df)),
        'funding': float(cluster_df['total_lifetime_funding'].sum()),
        'lead_ic': str(cluster_df['ic_name'].mode()[0] if len(cluster_df) > 0 else 'Unknown'),
        'centroid_x': float(cluster_df['umap_x_improved'].mean()),
        'centroid_y': float(cluster_df['umap_y_improved'].mean())
    }

df['cluster_label_improved'] = df['cluster_umap_k75'].map(
    lambda x: cluster_info[str(x)]['label']
)

# Save improved dataset
df.to_csv('awards_110k_improved_clustering.csv', index=False)
print("\n✅ Saved: awards_110k_improved_clustering.csv")

# Create visualization
print("\nCreating interactive map...")

sample_size = min(50000, len(df))
df_viz = df.sample(n=sample_size, random_state=42)

viz_data = {
    'x': df_viz['umap_x_improved'].tolist(),
    'y': df_viz['umap_y_improved'].tolist(),
    'cluster': df_viz['cluster_umap_k75'].tolist(),
    'labels': df_viz['cluster_label_improved'].tolist(),
    'funding': df_viz['total_lifetime_funding'].tolist(),
    'ic': df_viz['ic_name'].tolist(),
    'activity': df_viz['activity'].tolist(),
    'title': df_viz['project_title'].tolist()
}

html_content = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>NIH Award Map - Improved Clustering</title>
    <script src="https://cdn.plot.ly/plotly-2.27.0.min.js"></script>
    <style>
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
            margin: 0;
            padding: 20px;
            background: #f5f5f5;
        }
        .header {
            background: white;
            padding: 20px;
            border-radius: 8px;
            margin-bottom: 20px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        h1 {
            margin: 0 0 10px 0;
            color: #1a1a1a;
        }
        .stats {
            color: #666;
            font-size: 14px;
            margin-bottom: 10px;
        }
        .method {
            background: #e3f2fd;
            padding: 10px;
            border-radius: 4px;
            font-size: 13px;
            color: #1565c0;
        }
        #plotDiv {
            background: white;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        .info-panel {
            background: white;
            padding: 20px;
            border-radius: 8px;
            margin-top: 20px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        .cluster-card {
            border: 1px solid #e0e0e0;
            padding: 12px;
            margin: 8px 0;
            border-radius: 4px;
            background: #fafafa;
        }
        .cluster-card h3 {
            margin: 0 0 8px 0;
            color: #1a1a1a;
            font-size: 16px;
        }
        .cluster-stat {
            display: inline-block;
            margin-right: 20px;
            color: #666;
            font-size: 13px;
        }
    </style>
</head>
<body>
    <div class="header">
        <h1>NIH Award Portfolio: Improved Semantic Clustering</h1>
        <div class="stats">
            <strong>103,204 awards</strong> | 
            <strong>75 clusters</strong> | 
            <strong>FY 2000-2024</strong> | 
            <strong>$179.7B total funding</strong>
        </div>
        <div class="method">
            Method: UMAP (n_neighbors=50, min_dist=0.0) + K-means in 2D space
        </div>
    </div>
    
    <div id="plotDiv"></div>
    
    <div class="info-panel">
        <h2>Top 10 Clusters by Funding</h2>
        <div id="topClusters"></div>
    </div>

    <script>
"""

html_content += f"""
        const data = {json.dumps(viz_data)};
        const clusterInfo = {json.dumps(cluster_info)};
"""

html_content += """
        const trace = {
            x: data.x,
            y: data.y,
            mode: 'markers',
            type: 'scatter',
            marker: {
                size: 3,
                color: data.cluster,
                colorscale: 'Viridis',
                showscale: true,
                colorbar: {
                    title: 'Cluster',
                    thickness: 15,
                    len: 0.7
                },
                opacity: 0.7,
                line: {
                    width: 0.5,
                    color: 'white'
                }
            },
            text: data.cluster.map((c, i) => 
                '<b>Cluster ' + c + ': ' + data.labels[i] + '</b><br>' +
                'IC: ' + data.ic[i] + '<br>' +
                'Activity: ' + data.activity[i] + '<br>' +
                'Funding: $' + (data.funding[i]/1e6).toFixed(1) + 'M<br>' +
                'Title: ' + data.title[i].substring(0, 80) + '...'
            ),
            hovertemplate: '%{text}<extra></extra>'
        };

        const annotations = [];
        Object.keys(clusterInfo).forEach(cid => {
            const info = clusterInfo[cid];
            annotations.push({
                x: info.centroid_x,
                y: info.centroid_y,
                text: '<b>' + cid + '</b>',
                showarrow: false,
                font: {
                    size: 11,
                    color: 'white',
                    family: 'Arial Black'
                },
                bgcolor: 'rgba(0, 0, 0, 0.7)',
                bordercolor: 'white',
                borderwidth: 2,
                borderpad: 4
            });
        });

        const layout = {
            title: {
                text: 'NIH Awards: UMAP Projection with Improved Parameters',
                font: { size: 18 }
            },
            xaxis: {
                title: 'UMAP 1',
                showgrid: false,
                zeroline: false
            },
            yaxis: {
                title: 'UMAP 2',
                showgrid: false,
                zeroline: false
            },
            hovermode: 'closest',
            height: 900,
            plot_bgcolor: '#1a1a1a',
            paper_bgcolor: 'white',
            annotations: annotations
        };

        const config = {
            responsive: true,
            displayModeBar: true,
            modeBarButtonsToRemove: ['lasso2d', 'select2d'],
            displaylogo: false
        };

        Plotly.newPlot('plotDiv', [trace], layout, config);

        const sortedClusters = Object.entries(clusterInfo)
            .map(([id, info]) => Object.assign({id: id}, info))
            .sort((a, b) => b.funding - a.funding)
            .slice(0, 10);

        const topClustersHTML = sortedClusters.map((c, i) => 
            '<div class="cluster-card">' +
                '<h3>' + (i+1) + '. Cluster ' + c.id + ': ' + c.label + '</h3>' +
                '<span class="cluster-stat"><strong>' + c.n_awards.toLocaleString() + '</strong> awards</span>' +
                '<span class="cluster-stat"><strong>$' + (c.funding/1e9).toFixed(2) + 'B</strong> funding</span>' +
                '<span class="cluster-stat">Lead IC: <strong>' + c.lead_ic.substring(0, 40) + '</strong></span>' +
            '</div>'
        ).join('');

        document.getElementById('topClusters').innerHTML = topClustersHTML;
    </script>
</body>
</html>
"""

with open('award_map_improved_interactive.html', 'w') as f:
    f.write(html_content)

print("✅ Saved: award_map_improved_interactive.html")

print("\n" + "="*70)
print("IMPROVED MAP COMPLETE!")
print("="*70)
print("\nKey improvements:")
print("  ✅ UMAP with n_neighbors=50 (was PCA)")
print("  ✅ min_dist=0.0 for tighter clusters")
print("  ✅ Clustering in 2D UMAP space")
print("  ✅ Dark background like original map")
print("  ✅ White-bordered cluster labels")
print("\nThis should look much more like the original NIH map!")
print("="*70)
