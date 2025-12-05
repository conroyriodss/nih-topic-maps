#!/usr/bin/env python3
"""
Create advanced interactive visualization with filtering and controls
"""

import pandas as pd
import numpy as np
import json
import plotly.graph_objects as go
from plotly.subplots import make_subplots

print("Loading data...")
# Load embeddings with UMAP coordinates
df = pd.read_parquet('https://storage.googleapis.com/od-cl-odss-conroyri-nih-embeddings/sample/umap_coordinates_50k.parquet')

# Load full data for additional fields
full_df = pd.read_parquet('https://storage.googleapis.com/od-cl-odss-conroyri-nih-embeddings/sample/embeddings_pubmedbert_50k.parquet')

# Merge
df = df.merge(full_df[['APPLICATION_ID', 'PROJECT_TITLE', 'FISCAL_YEAR', 'IC_NAME', 'TOTAL_COST']], 
              on='APPLICATION_ID', how='left')

print(f"Loaded {len(df):,} grants")

# Create color mappings
# For ICs - use categorical colors
ic_list = sorted(df['IC_NAME'].unique())
ic_colors = {ic: i for i, ic in enumerate(ic_list)}
df['ic_color'] = df['IC_NAME'].map(ic_colors)

# For years - use continuous scale
df['year_color'] = df['FISCAL_YEAR']

# For topics - use categorical
df['topic_color'] = df['topic']

# Create hover text
df['hover_text'] = (
    '<b>' + df['PROJECT_TITLE'].str[:100] + '</b><br>' +
    '<b>Topic:</b> ' + df['topic_label'] + '<br>' +
    '<b>IC:</b> ' + df['IC_NAME'] + '<br>' +
    '<b>Year:</b> ' + df['FISCAL_YEAR'].astype(str) + '<br>' +
    '<b>Funding:</b> $' + (df['TOTAL_COST'] / 1e6).round(2).astype(str) + 'M<br>' +
    '<b>ID:</b> ' + df['APPLICATION_ID']
)

print("Creating visualization...")

# Create figure with custom controls
fig = go.Figure()

# Add trace for each IC (so we can toggle)
for ic in ic_list:
    ic_data = df[df['IC_NAME'] == ic]
    
    fig.add_trace(go.Scattergl(
        x=ic_data['umap_x'],
        y=ic_data['umap_y'],
        mode='markers',
        name=ic,
        text=ic_data['hover_text'],
        hovertemplate='%{text}<extra></extra>',
        marker=dict(
            size=3,
            opacity=0.6,
            line=dict(width=0)
        ),
        visible=True
    ))

# Update layout with controls
fig.update_layout(
    title={
        'text': 'NIH Grant Topic Map - 50K Sample (2000-2024)<br><sub>Color by IC | Toggle ICs | Hover for details</sub>',
        'x': 0.5,
        'xanchor': 'center',
        'font': {'size': 20}
    },
    xaxis_title='UMAP Dimension 1',
    yaxis_title='UMAP Dimension 2',
    width=1600,
    height=1000,
    hovermode='closest',
    plot_bgcolor='white',
    paper_bgcolor='white',
    font=dict(size=12),
    showlegend=True,
    legend=dict(
        title='NIH Institutes/Centers<br><sub>Click to toggle</sub>',
        yanchor="top",
        y=0.99,
        xanchor="left",
        x=1.01,
        bgcolor='rgba(255,255,255,0.9)',
        bordercolor='#ddd',
        borderwidth=1,
        font=dict(size=10)
    ),
    updatemenus=[
        # Color by selector
        dict(
            buttons=[
                dict(label="Color by IC",
                     method="restyle",
                     args=["visible", [True] * len(ic_list)]),
                dict(label="Color by Year",
                     method="update",
                     args=[{"visible": [False] * len(ic_list)},
                           {"title": "Colored by Year - Coming soon"}]),
                dict(label="Color by Topic",
                     method="update",
                     args=[{"visible": [False] * len(ic_list)},
                           {"title": "Colored by Topic - Coming soon"}])
            ],
            direction="down",
            pad={"r": 10, "t": 10},
            showactive=True,
            x=0.01,
            xanchor="left",
            y=1.15,
            yanchor="top",
            bgcolor='white',
            bordercolor='#ddd',
            borderwidth=1
        ),
    ]
)

# Save
html_file = 'data/processed/topic_map_advanced.html'
fig.write_html(html_file, config={
    'scrollZoom': True,
    'displayModeBar': True,
    'displaylogo': False,
    'modeBarButtonsToRemove': ['lasso2d', 'select2d']
})

print(f"✓ Saved to {html_file}")

# Upload
import subprocess
subprocess.run([
    'gsutil', 'cp', html_file,
    'gs://od-cl-odss-conroyri-nih-embeddings/sample/'
], check=True)

print("✓ Uploaded to GCS")
print("\nView at:")
print("https://storage.googleapis.com/od-cl-odss-conroyri-nih-embeddings/sample/topic_map_advanced.html")
