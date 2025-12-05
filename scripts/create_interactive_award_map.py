#!/usr/bin/env python3
"""
Create interactive HTML visualization of award-level semantic clustering
"""
import pandas as pd
import numpy as np
import json
from sklearn.feature_extraction.text import TfidfVectorizer

print("="*70)
print("CREATING INTERACTIVE AWARD CLUSTER MAP")
print("="*70)

# Load data
print("\n[1/4] Loading clustered awards...")
df = pd.read_csv('awards_110k_with_semantic_clusters.csv')
print(f"Loaded {len(df):,} awards with semantic clusters")

# Generate cluster labels
print("\n[2/4] Generating cluster labels...")
cluster_info = {}

for cluster_id in sorted(df['cluster_semantic_k75'].unique()):
    cluster_df = df[cluster_id == df['cluster_semantic_k75']]
    
    # Extract keywords
    vec = TfidfVectorizer(max_features=5, stop_words='english', ngram_range=(1,2))
    titles_combined = ' '.join(cluster_df['project_title'].head(100).tolist())
    
    try:
        vec.fit([titles_combined])
        keywords = ' & '.join([k.title() for k in vec.get_feature_names_out()[:3]])
    except:
        keywords = f'Cluster {cluster_id}'
    
    cluster_info[str(cluster_id)] = {
        'label': keywords,
        'n_awards': int(len(cluster_df)),
        'funding': float(cluster_df['total_lifetime_funding'].sum()),
        'lead_ic': str(cluster_df['ic_name'].mode()[0] if len(cluster_df) > 0 else 'Unknown'),
        'top_activity': str(cluster_df['activity'].mode()[0] if len(cluster_df) > 0 else 'Unknown'),
        'centroid_x': float(cluster_df['umap_x'].mean()),
        'centroid_y': float(cluster_df['umap_y'].mean())
    }

# Add cluster labels to dataframe
df['cluster_label'] = df['cluster_semantic_k75'].map(lambda x: cluster_info[str(x)]['label'])

# Sample for visualization
print("\n[3/4] Sampling data for visualization...")
sample_size = min(50000, len(df))
df_viz = df.sample(n=sample_size, random_state=42)
print(f"Using {len(df_viz):,} awards for interactive visualization")

# Prepare data for JSON
viz_data = {
    'x': df_viz['umap_x'].tolist(),
    'y': df_viz['umap_y'].tolist(),
    'cluster': df_viz['cluster_semantic_k75'].tolist(),
    'labels': df_viz['cluster_label'].tolist(),
    'funding': df_viz['total_lifetime_funding'].tolist(),
    'ic': df_viz['ic_name'].tolist(),
    'activity': df_viz['activity'].tolist(),
    'title': df_viz['project_title'].tolist()
}

# Create HTML
print("\n[4/4] Generating interactive HTML...")

html_content = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>NIH Award Semantic Clustering - Interactive Map</title>
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
        <h1>NIH Award Portfolio: Semantic Clustering</h1>
        <div class="stats">
            <strong>103,204 awards</strong> | 
            <strong>75 semantic clusters</strong> | 
            <strong>FY 2000-2024</strong> | 
            <strong>$179.7B total funding</strong>
        </div>
    </div>
    
    <div id="plotDiv"></div>
    
    <div class="info-panel">
        <h2>Top 10 Clusters by Funding</h2>
        <div id="topClusters"></div>
    </div>

    <script>
"""

# Add data as JSON
html_content += f"""
        const data = {json.dumps(viz_data)};
        const clusterInfo = {json.dumps(cluster_info)};
"""

html_content += """
        // Create scatter plot
        const trace = {
            x: data.x,
            y: data.y,
            mode: 'markers',
            type: 'scatter',
            marker: {
                size: 4,
                color: data.cluster,
                colorscale: 'Viridis',
                showscale: true,
                colorbar: {
                    title: 'Cluster',
                    thickness: 15,
                    len: 0.7
                },
                opacity: 0.6,
                line: {
                    width: 0
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

        // Add cluster centroid labels
        const annotations = [];
        Object.keys(clusterInfo).forEach(cid => {
            const info = clusterInfo[cid];
            annotations.push({
                x: info.centroid_x,
                y: info.centroid_y,
                text: '<b>' + cid + '</b>',
                showarrow: false,
                font: {
                    size: 10,
                    color: '#1a1a1a'
                },
                bgcolor: 'rgba(255, 255, 255, 0.8)',
                bordercolor: '#666',
                borderwidth: 1,
                borderpad: 4
            });
        });

        const layout = {
            title: {
                text: 'Semantic Clusters of NIH Research Awards',
                font: { size: 18 }
            },
            xaxis: {
                title: 'Dimension 1',
                showgrid: true,
                zeroline: false
            },
            yaxis: {
                title: 'Dimension 2',
                showgrid: true,
                zeroline: false
            },
            hovermode: 'closest',
            height: 800,
            plot_bgcolor: '#fafafa',
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

        // Generate top clusters list
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

# Save HTML
with open('award_semantic_map_interactive.html', 'w') as f:
    f.write(html_content)

print("   ✅ Saved: award_semantic_map_interactive.html")

print("\n" + "="*70)
print("INTERACTIVE MAP COMPLETE!")
print("="*70)
print("\nOpen the file in your browser:")
print("  award_semantic_map_interactive.html")
print("\nFeatures:")
print("  • Hover over points to see award details")
print("  • Zoom and pan to explore clusters")
print("  • Cluster centroids labeled with IDs")
print("  • Top 10 clusters listed below map")
print("  • 50,000 awards visualized (sampled from 103K)")
print("="*70)
