#!/usr/bin/env python3
"""
Create award-level map by aggregating existing transaction embeddings
"""
import pandas as pd
import numpy as np
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score
from sklearn.feature_extraction.text import TfidfVectorizer
import json

print("="*70)
print("CREATING AWARD MAP FROM TRANSACTION EMBEDDINGS")
print("="*70)

# Load transaction data
print("\n[1/5] Loading transaction data...")
df_trans = pd.read_csv('hierarchical_250k_clustered_k75.csv')
print(f"Loaded {len(df_trans):,} transactions")
print(f"Columns: {df_trans.columns.tolist()}")

# Aggregate to award level
print(f"\n[2/5] Aggregating transactions to awards by APPLICATION_ID...")

award_coords = df_trans.groupby('APPLICATION_ID').agg({
    'umap_x': 'mean',
    'umap_y': 'mean',
    'TOTAL_COST': 'sum',
    'IC_NAME': lambda x: x.mode()[0] if len(x) > 0 else 'Unknown',
    'PROJECT_TITLE': 'first',
    'FY': 'max'
}).reset_index()

print(f"Created {len(award_coords):,} unique awards from transactions")
print(f"UMAP X range: [{award_coords['umap_x'].min():.2f}, {award_coords['umap_x'].max():.2f}]")
print(f"UMAP Y range: [{award_coords['umap_y'].min():.2f}, {award_coords['umap_y'].max():.2f}]")

# Cluster in 2D UMAP space
print("\n[3/5] Clustering awards in 2D UMAP space...")

coords_2d = award_coords[['umap_x', 'umap_y']].values

kmeans = KMeans(
    n_clusters=75,
    random_state=42,
    n_init=20,
    max_iter=500
)

award_coords['cluster_k75'] = kmeans.fit_predict(coords_2d)

silhouette = silhouette_score(coords_2d, award_coords['cluster_k75'], sample_size=10000)
print(f"   Silhouette score: {silhouette:.4f}")
print(f"   Clusters: {award_coords['cluster_k75'].nunique()}")

# Generate cluster labels
print("\n[4/5] Generating cluster labels...")

cluster_info = {}
for cluster_id in sorted(award_coords['cluster_k75'].unique()):
    cluster_df = award_coords[award_coords['cluster_k75'] == cluster_id]
    
    # Extract keywords
    vec = TfidfVectorizer(max_features=5, stop_words='english', ngram_range=(1,2))
    titles = ' '.join(cluster_df['PROJECT_TITLE'].dropna().head(100).tolist())
    
    try:
        vec.fit([titles])
        keywords = ' & '.join([k.title() for k in vec.get_feature_names_out()[:3]])
    except:
        keywords = f'Cluster {cluster_id}'
    
    cluster_info[str(cluster_id)] = {
        'label': keywords,
        'n_awards': int(len(cluster_df)),
        'funding': float(cluster_df['TOTAL_COST'].sum()),
        'lead_ic': str(cluster_df['IC_NAME'].mode()[0] if len(cluster_df) > 0 else 'Unknown'),
        'centroid_x': float(cluster_df['umap_x'].mean()),
        'centroid_y': float(cluster_df['umap_y'].mean())
    }

award_coords['cluster_label'] = award_coords['cluster_k75'].map(
    lambda x: cluster_info[str(x)]['label']
)

# Save
award_coords.to_csv('awards_from_transactions_clustered.csv', index=False)
print("   ✅ Saved: awards_from_transactions_clustered.csv")

# Summary stats
print("\n" + "="*70)
print("CLUSTER SUMMARY")
print("="*70)
top10 = pd.DataFrame(cluster_info).T.sort_values('funding', ascending=False).head(10)
for idx, row in top10.iterrows():
    print(f"Cluster {idx:2s}: {row['label'][:50]:<50} | {row['n_awards']:>5} awards | ${row['funding']/1e9:>5.1f}B")

# Create interactive visualization
print("\n[5/5] Creating interactive visualization...")

sample_size = min(50000, len(award_coords))
df_viz = award_coords.sample(n=sample_size, random_state=42) if len(award_coords) > sample_size else award_coords

viz_data = {
    'x': df_viz['umap_x'].tolist(),
    'y': df_viz['umap_y'].tolist(),
    'cluster': df_viz['cluster_k75'].tolist(),
    'labels': df_viz['cluster_label'].tolist(),
    'funding': df_viz['TOTAL_COST'].tolist(),
    'ic': df_viz['IC_NAME'].tolist(),
    'fy': df_viz['FY'].tolist(),
    'title': df_viz['PROJECT_TITLE'].tolist()
}

html_content = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>NIH Award Map - From Transaction Embeddings</title>
    <script src="https://cdn.plot.ly/plotly-2.27.0.min.js"></script>
    <style>
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
            margin: 0;
            padding: 0;
            background: #0a0a0a;
            color: white;
        }
        .header {
            background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
            padding: 30px;
            border-bottom: 3px solid #0f3460;
        }
        h1 {
            margin: 0 0 10px 0;
            color: #eaeaea;
            font-size: 28px;
        }
        .stats {
            color: #a8dadc;
            font-size: 15px;
            margin-bottom: 10px;
        }
        .method {
            background: rgba(15, 52, 96, 0.5);
            padding: 12px;
            border-radius: 6px;
            font-size: 13px;
            color: #81b7d2;
            border-left: 3px solid #0f3460;
        }
        #plotDiv {
            background: #0a0a0a;
        }
        .info-panel {
            background: #1a1a2e;
            padding: 30px;
            border-top: 3px solid #0f3460;
        }
        .info-panel h2 {
            color: #eaeaea;
            margin-top: 0;
        }
        .cluster-card {
            border: 1px solid #0f3460;
            padding: 15px;
            margin: 10px 0;
            border-radius: 6px;
            background: #16213e;
            transition: all 0.3s;
        }
        .cluster-card:hover {
            background: #1a2a4e;
            border-color: #1e5a8e;
        }
        .cluster-card h3 {
            margin: 0 0 10px 0;
            color: #a8dadc;
            font-size: 17px;
        }
        .cluster-stat {
            display: inline-block;
            margin-right: 20px;
            color: #81b7d2;
            font-size: 13px;
        }
    </style>
</head>
<body>
    <div class="header">
        <h1>🔬 NIH Award Portfolio: Semantic Clustering</h1>
        <div class="stats">
            """ + f"<strong>{len(award_coords):,} unique awards</strong> | " + """
            <strong>75 clusters</strong> | 
            <strong>FY 2000-2024</strong> | 
            """ + f"<strong>${award_coords['TOTAL_COST'].sum()/1e9:.1f}B total funding</strong>" + """
        </div>
        <div class="method">
            ✨ Method: Awards aggregated from transaction-level PubMedBERT embeddings (UMAP: n_neighbors=50, min_dist=0.0)
        </div>
    </div>
    
    <div id="plotDiv"></div>
    
    <div class="info-panel">
        <h2>🏆 Top 10 Clusters by Funding</h2>
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
            type: 'scattergl',
            marker: {
                size: 3.5,
                color: data.cluster,
                colorscale: 'Viridis',
                showscale: true,
                colorbar: {
                    title: {
                        text: 'Cluster',
                        font: {color: '#eaeaea'}
                    },
                    tickfont: {color: '#eaeaea'},
                    thickness: 20,
                    len: 0.7
                },
                opacity: 0.8,
                line: {
                    width: 0.5,
                    color: 'rgba(255, 255, 255, 0.3)'
                }
            },
            text: data.cluster.map((c, i) => 
                '<b>Cluster ' + c + ': ' + data.labels[i] + '</b><br>' +
                'IC: ' + data.ic[i] + '<br>' +
                'FY: ' + data.fy[i] + '<br>' +
                'Funding: $' + (data.funding[i]/1e6).toFixed(1) + 'M<br>' +
                'Title: ' + data.title[i].substring(0, 80) + '...'
            ),
            hovertemplate: '<span style="color: #a8dadc">%{text}</span><extra></extra>'
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
                    size: 12,
                    color: 'white',
                    family: 'Arial Black'
                },
                bgcolor: 'rgba(15, 52, 96, 0.9)',
                bordercolor: '#a8dadc',
                borderwidth: 2,
                borderpad: 5
            });
        });

        const layout = {
            title: {
                text: 'NIH Research Awards: UMAP Projection (Award-Level View)',
                font: { size: 20, color: '#eaeaea' }
            },
            xaxis: {
                title: 'UMAP Dimension 1',
                showgrid: false,
                zeroline: false,
                color: '#81b7d2'
            },
            yaxis: {
                title: 'UMAP Dimension 2',
                showgrid: false,
                zeroline: false,
                color: '#81b7d2'
            },
            hovermode: 'closest',
            height: 900,
            plot_bgcolor: '#0a0a0a',
            paper_bgcolor: '#0a0a0a',
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
                '<span class="cluster-stat">📊 <strong>' + c.n_awards.toLocaleString() + '</strong> awards</span>' +
                '<span class="cluster-stat">💰 <strong>$' + (c.funding/1e9).toFixed(2) + 'B</strong></span>' +
                '<span class="cluster-stat">🏛️ <strong>' + c.lead_ic.substring(0, 35) + '</strong></span>' +
            '</div>'
        ).join('');

        document.getElementById('topClusters').innerHTML = topClustersHTML;
    </script>
</body>
</html>
"""

with open('award_map_from_transactions.html', 'w') as f:
    f.write(html_content)

print("   ✅ Saved: award_map_from_transactions.html")

print("\n" + "="*70)
print("✅ AWARD MAP COMPLETE!")
print("="*70)
print(f"\nUnique awards: {len(award_coords):,}")
print(f"Clusters: {award_coords['cluster_k75'].nunique()}")
print(f"Total funding: ${award_coords['TOTAL_COST'].sum()/1e9:.1f}B")
print(f"Silhouette: {silhouette:.4f}")
print("\nThis map uses the SAME UMAP coordinates as your transaction map!")
print("Cluster structure should match the original NIH map structure.")
print("="*70)
