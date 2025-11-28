#!/usr/bin/env python3
"""
Create interactive HTML visualization for PROJECT_TERMS clustering
"""

import json
import subprocess

print("\n" + "="*70)
print("Creating Interactive PROJECT_TERMS Visualization")
print("="*70 + "\n")

# Download visualization data
print("Downloading visualization data from GCS...")
subprocess.run([
    'gsutil', 'cp',
    'gs://od-cl-odss-conroyri-nih-embeddings/sample/viz_data_project_terms_k100.json',
    'data/processed/'
], check=True)

# Load data
print("Loading visualization data...")
with open('data/processed/viz_data_project_terms_k100.json') as f:
    viz_data = json.load(f)

print(f"Points: {len(viz_data['points']):,}")
print(f"Clusters: {len(viz_data['clusters'])}")

# Convert to JSON string for embedding
viz_data_json = json.dumps(viz_data)

# Create HTML file
html_content = f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>NIH Topic Maps - PROJECT_TERMS K=100</title>
    <script src="https://d3js.org/d3.v7.min.js"></script>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
            background: #f5f7fa;
        }}
        
        .container {{
            display: flex;
            height: 100vh;
        }}
        
        .header {{
            position: fixed;
            top: 0;
            left: 0;
            right: 0;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 20px;
            z-index: 100;
            box-shadow: 0 2px 8px rgba(0,0,0,0.15);
        }}
        
        .header h1 {{
            margin: 0;
            font-size: 24px;
        }}
        
        .header p {{
            margin: 5px 0 0 0;
            font-size: 13px;
            opacity: 0.9;
        }}
        
        .main {{
            display: flex;
            width: 100%;
            margin-top: 80px;
        }}
        
        .sidebar {{
            width: 350px;
            background: white;
            border-right: 1px solid #e0e0e0;
            overflow-y: auto;
            padding: 20px;
        }}
        
        .sidebar h2 {{
            font-size: 14px;
            color: #666;
            text-transform: uppercase;
            margin-bottom: 15px;
            margin-top: 20px;
        }}
        
        .sidebar h2:first-child {{
            margin-top: 0;
        }}
        
        .cluster-item {{
            background: #f8f9fa;
            padding: 12px;
            margin-bottom: 8px;
            border-radius: 6px;
            cursor: pointer;
            border-left: 3px solid #ddd;
            font-size: 13px;
            transition: all 0.2s;
        }}
        
        .cluster-item:hover {{
            background: #f0f2f5;
            border-left-color: #667eea;
        }}
        
        .cluster-item.active {{
            background: #e6e9ff;
            border-left-color: #667eea;
        }}
        
        .cluster-name {{
            font-weight: 500;
            color: #333;
            margin-bottom: 4px;
        }}
        
        .cluster-size {{
            font-size: 12px;
            color: #999;
        }}
        
        .viz-container {{
            flex: 1;
            position: relative;
        }}
        
        svg {{
            width: 100%;
            height: 100%;
        }}
        
        .point {{
            cursor: pointer;
            stroke: white;
            stroke-width: 0.5px;
            transition: all 0.2s;
        }}
        
        .point:hover {{
            stroke-width: 2px;
            filter: brightness(1.2);
        }}
        
        .point.highlighted {{
            stroke: #333;
            stroke-width: 2px;
        }}
        
        .tooltip {{
            position: absolute;
            background: rgba(0, 0, 0, 0.95);
            color: white;
            padding: 12px 15px;
            border-radius: 6px;
            font-size: 12px;
            pointer-events: none;
            z-index: 50;
            max-width: 300px;
            box-shadow: 0 4px 12px rgba(0,0,0,0.25);
            display: none;
        }}
        
        .tooltip-title {{
            font-weight: 600;
            margin-bottom: 8px;
            color: #667eea;
        }}
        
        .tooltip-item {{
            margin: 4px 0;
        }}
        
        .tooltip-label {{
            color: #aaa;
            display: inline-block;
            width: 70px;
        }}
        
        .stats {{
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 10px;
            margin-bottom: 20px;
        }}
        
        .stat-box {{
            background: #f8f9fa;
            padding: 15px;
            border-radius: 6px;
            text-align: center;
        }}
        
        .stat-value {{
            font-size: 20px;
            font-weight: bold;
            color: #667eea;
        }}
        
        .stat-label {{
            font-size: 11px;
            color: #999;
            margin-top: 5px;
        }}
        
        .info-section {{
            background: #f8f9fa;
            padding: 15px;
            border-radius: 6px;
            margin-bottom: 15px;
            border-left: 3px solid #667eea;
        }}
        
        .info-section h3 {{
            font-size: 12px;
            font-weight: 600;
            margin-bottom: 8px;
            color: #333;
        }}
        
        .info-section p {{
            font-size: 12px;
            color: #666;
            line-height: 1.4;
        }}
    </style>
</head>
<body>
    <div class="header">
        <h1>🧬 NIH Topic Maps - PROJECT_TERMS Clustering</h1>
        <p>43,320 grants across 100 topics | K-means on PubMedBERT embeddings</p>
    </div>
    
    <div class="main">
        <div class="sidebar">
            <div class="stats">
                <div class="stat-box">
                    <div class="stat-value">43,320</div>
                    <div class="stat-label">Grants</div>
                </div>
                <div class="stat-box">
                    <div class="stat-value">100</div>
                    <div class="stat-label">Topics</div>
                </div>
                <div class="stat-box">
                    <div class="stat-value">0.0391</div>
                    <div class="stat-label">Silhouette</div>
                </div>
                <div class="stat-box">
                    <div class="stat-value">20.8</div>
                    <div class="stat-label">Avg ICs</div>
                </div>
            </div>
            
            <div class="info-section">
                <h3>About This Visualization</h3>
                <p>Interactive UMAP projection of NIH grants clustered by research topic using PROJECT_TERMS keywords. Hover over points for details.</p>
            </div>
            
            <h2>Topics</h2>
            <div id="cluster-list"></div>
        </div>
        
        <div class="viz-container">
            <svg id="viz"></svg>
            <div class="tooltip" id="tooltip"></div>
        </div>
    </div>
    
    <script>
        // Embedded visualization data
        const vizData = {viz_data_json};
        
        // Setup
        const margin = {{top: 20, right: 20, bottom: 20, left: 20}};
        const width = document.querySelector('.viz-container').clientWidth - margin.left - margin.right;
        const height = window.innerHeight - 100 - margin.top - margin.bottom;
        
        // Create scales
        const xExtent = d3.extent(vizData.points, d => d.x);
        const yExtent = d3.extent(vizData.points, d => d.y);
        
        const xScale = d3.scaleLinear()
            .domain(xExtent)
            .range([0, width]);
        
        const yScale = d3.scaleLinear()
            .domain(yExtent)
            .range([height, 0]);
        
        // Color scale for clusters
        const colorScale = d3.scaleOrdinal(d3.schemeCategory10)
            .domain(d3.range(100));
        
        // Create SVG
        const svg = d3.select('#viz')
            .attr('width', width + margin.left + margin.right)
            .attr('height', height + margin.top + margin.bottom)
            .append('g')
            .attr('transform', `translate(${{margin.left}},${{margin.top}})`);
        
        // Draw points
        const points = svg.selectAll('.point')
            .data(vizData.points)
            .enter()
            .append('circle')
            .attr('class', 'point')
            .attr('cx', d => xScale(d.x))
            .attr('cy', d => yScale(d.y))
            .attr('r', 3)
            .attr('fill', d => colorScale(d.cluster))
            .attr('opacity', 0.7)
            .on('mouseover', function(event, d) {{
                showTooltip(event, d);
                d3.select(this).classed('highlighted', true);
            }})
            .on('mouseout', function(event, d) {{
                hideTooltip();
                d3.select(this).classed('highlighted', false);
            }})
            .on('click', function(event, d) {{
                highlightCluster(d.cluster);
            }});
        
        // Populate cluster list
        const clusterList = document.getElementById('cluster-list');
        vizData.clusters.forEach(cluster => {{
            const item = document.createElement('div');
            item.className = 'cluster-item';
            item.innerHTML = `
                <div class="cluster-name">${{cluster.label}}</div>
                <div class="cluster-size">${{cluster.size}} grants</div>
            `;
            item.onclick = () => highlightCluster(cluster.id);
            clusterList.appendChild(item);
        }});
        
        // Tooltip functions
        function showTooltip(event, d) {{
            const tooltip = document.getElementById('tooltip');
            tooltip.innerHTML = `
                <div class="tooltip-title">${{d.title || 'Grant ' + d.application_id}}</div>
                <div class="tooltip-item">
                    <span class="tooltip-label">ID:</span>
                    <span>${{d.application_id}}</span>
                </div>
                <div class="tooltip-item">
                    <span class="tooltip-label">Cluster:</span>
                    <span>${{d.cluster}}</span>
                </div>
                <div class="tooltip-item">
                    <span class="tooltip-label">IC:</span>
                    <span>${{d.ic}}</span>
                </div>
                <div class="tooltip-item">
                    <span class="tooltip-label">Year:</span>
                    <span>${{d.year}}</span>
                </div>
                <div class="tooltip-item">
                    <span class="tooltip-label">Cost:</span>
                    <span>${{(d.cost / 1000000).toFixed(1)}}M</span>
                </div>
            `;
            tooltip.style.display = 'block';
            tooltip.style.left = (event.pageX + 10) + 'px';
            tooltip.style.top = (event.pageY + 10) + 'px';
        }}
        
        function hideTooltip() {{
            document.getElementById('tooltip').style.display = 'none';
        }}
        
        function highlightCluster(clusterId) {{
            points.classed('highlighted', d => d.cluster === clusterId)
                .attr('r', d => d.cluster === clusterId ? 5 : 3)
                .attr('opacity', d => d.cluster === clusterId ? 0.9 : 0.3);
            
            document.querySelectorAll('.cluster-item').forEach((item, i) => {{
                item.classList.toggle('active', i === clusterId);
            }});
        }}
    </script>
</body>
</html>
'''

# Save HTML file
output_file = 'project_terms_viz.html'
with open(output_file, 'w') as f:
    f.write(html_content)

print(f"\nSaved: {output_file}")

# Upload to GCS
print("Uploading to GCS...")
subprocess.run(['gsutil', 'cp', output_file, 'gs://od-cl-odss-conroyri-nih-embeddings/sample/'], check=True)

print("\n" + "="*70)
print("VISUALIZATION CREATED!")
print("="*70)
print(f"\nLocal file: {output_file}")
print(f"\nGCS link:")
print(f"https://storage.googleapis.com/od-cl-odss-conroyri-nih-embeddings/sample/{output_file}")
print(f"\nFeatures:")
print("  - Interactive UMAP scatter plot")
print("  - Hover tooltips with grant details")
print("  - Click clusters to highlight")
print("  - 100 topics with auto-generated labels")
print("  - 43,320 grants visualized")
