#!/bin/bash

# NIH Topic Maps - Deployment Script
# Deploys interactive visualization to GCS
# Usage: bash deploy_viz.sh

set -e

PROJECT_ID="od-cl-odss-conroyri-f75a"
BUCKET="gs://od-cl-odss-conroyri-nih-embeddings/sample"
LOCAL_DIR="${HOME}/nih-topic-maps"

echo "============================================================"
echo "NIH TOPIC MAPS - VISUALIZATION DEPLOYMENT"
echo "============================================================"
echo ""

# Create HTML file
echo "[1/4] Creating HTML file..."
cat > "${LOCAL_DIR}/topic_map_hybrid.html" << 'HTMLEOF'
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>NIH Topic Map</title>
    <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
    <style>
        body { font-family: sans-serif; margin: 0; padding: 20px; background: #f5f5f5; }
        .container { max-width: 1400px; margin: 0 auto; background: white; padding: 20px; border-radius: 8px; }
        h1 { margin: 0 0 10px 0; }
        .subtitle { color: #666; margin-bottom: 20px; font-size: 14px; }
        .controls { margin-bottom: 20px; padding: 15px; background: #fafafa; border-radius: 4px; }
        .control-row { display: flex; gap: 20px; margin-bottom: 10px; flex-wrap: wrap; }
        label { font-size: 12px; font-weight: bold; display: block; margin-bottom: 4px; }
        select, input { padding: 6px 10px; border: 1px solid #ddd; border-radius: 4px; font-size: 13px; }
        button { padding: 8px 16px; background: #2563eb; color: white; border: none; border-radius: 4px; cursor: pointer; }
        #chart { height: 600px; }
        .stats { display: flex; gap: 30px; }
        .stat { text-align: center; }
        .stat-value { font-size: 18px; font-weight: bold; color: #2563eb; }
        .stat-label { font-size: 11px; color: #999; }
    </style>
</head>
<body>
    <div class="container">
        <h1>NIH Topic Map - Hybrid Clustering</h1>
        <div class="subtitle">50,000 grants (2000-2024) with PubMedBERT embeddings and RCDC categories</div>
        
        <div class="controls">
            <div class="control-row">
                <div>
                    <label>Color By</label>
                    <select id="colorBy" onchange="updateChart()">
                        <option value="topic">Topic</option>
                        <option value="ic">Institute</option>
                        <option value="funding">Funding</option>
                    </select>
                </div>
                <div>
                    <label>Year Range</label>
                    <div style="display: flex; gap: 5px;">
                        <input type="range" id="yearMin" min="2000" max="2024" value="2000" onchange="updateChart()">
                        <span id="yearLabel" style="min-width: 70px;">2000-2024</span>
                        <input type="range" id="yearMax" min="2000" max="2024" value="2024" onchange="updateChart()">
                    </div>
                </div>
                <div>
                    <label>Funding ($M)</label>
                    <div style="display: flex; gap: 5px;">
                        <input type="range" id="fundMin" min="0" max="50" value="0" onchange="updateChart()">
                        <span id="fundLabel" style="min-width: 70px;">0-50M</span>
                        <input type="range" id="fundMax" min="0" max="50" value="50" onchange="updateChart()">
                    </div>
                </div>
                <button onclick="resetFilters()">Reset</button>
            </div>
            <div class="control-row">
                <div style="flex: 1;">
                    <label>Search</label>
                    <input type="text" id="search" placeholder="Search titles..." onkeyup="updateChart()" style="width: 100%;">
                </div>
            </div>
            <div class="stats">
                <div class="stat">
                    <div class="stat-value" id="count">50000</div>
                    <div class="stat-label">Grants</div>
                </div>
                <div class="stat">
                    <div class="stat-value" id="funding">-</div>
                    <div class="stat-label">Total Funding</div>
                </div>
            </div>
        </div>
        
        <div id="chart"></div>
    </div>

    <script>
        let data = [];

        async function loadData() {
            const url = 'https://storage.googleapis.com/od-cl-odss-conroyri-nih-embeddings/sample/hybrid_viz_data.json';
            data = await fetch(url).then(r => r.json());
            console.log('Loaded', data.length, 'records');
            updateChart();
        }

        function updateChart() {
            const colorBy = document.getElementById('colorBy').value;
            const yearMin = parseInt(document.getElementById('yearMin').value);
            const yearMax = parseInt(document.getElementById('yearMax').value);
            const fundMin = parseInt(document.getElementById('fundMin').value);
            const fundMax = parseInt(document.getElementById('fundMax').value);
            const search = document.getElementById('search').value.toLowerCase();

            document.getElementById('yearLabel').textContent = yearMin + '-' + yearMax;
            document.getElementById('fundLabel').textContent = fundMin + '-' + fundMax + 'M';

            let filtered = data.filter(d => {
                if (d.year < yearMin || d.year > yearMax) return false;
                if (d.funding / 1e6 < fundMin || d.funding / 1e6 > fundMax) return false;
                if (search && !d.title.toLowerCase().includes(search)) return false;
                return true;
            });

            document.getElementById('count').textContent = filtered.length.toLocaleString();
            const total = filtered.reduce((s, d) => s + d.funding, 0);
            document.getElementById('funding').textContent = '$' + (total / 1e9).toFixed(2) + 'B';

            let traces = [];
            
            if (colorBy === 'topic') {
                const byTopic = {};
                filtered.forEach(d => {
                    if (!byTopic[d.topic]) byTopic[d.topic] = { x: [], y: [], text: [], label: d.topic_label };
                    byTopic[d.topic].x.push(d.x);
                    byTopic[d.topic].y.push(d.y);
                    byTopic[d.topic].text.push(d.title + '<br>' + d.topic_label);
                });
                
                Object.entries(byTopic).forEach(([id, g]) => {
                    traces.push({
                        x: g.x, y: g.y, text: g.text,
                        mode: 'markers', type: 'scattergl',
                        name: g.label.substring(0, 30),
                        marker: { size: 4, opacity: 0.6 },
                        hoverinfo: 'text'
                    });
                });
            } else if (colorBy === 'ic') {
                const byIC = {};
                filtered.forEach(d => {
                    if (!byIC[d.ic]) byIC[d.ic] = { x: [], y: [], text: [] };
                    byIC[d.ic].x.push(d.x);
                    byIC[d.ic].y.push(d.y);
                    byIC[d.ic].text.push(d.title);
                });
                
                Object.entries(byIC).forEach(([ic, g]) => {
                    traces.push({
                        x: g.x, y: g.y, text: g.text,
                        mode: 'markers', type: 'scattergl',
                        name: ic,
                        marker: { size: 4, opacity: 0.6 },
                        hoverinfo: 'text'
                    });
                });
            } else {
                traces.push({
                    x: filtered.map(d => d.x),
                    y: filtered.map(d => d.y),
                    text: filtered.map(d => d.title + '<br>$' + (d.funding/1e6).toFixed(1) + 'M'),
                    mode: 'markers', type: 'scattergl',
                    marker: {
                        size: 5, opacity: 0.6,
                        color: filtered.map(d => d.funding / 1e6),
                        colorscale: 'YlOrRd',
                        colorbar: { title: 'Funding ($M)' }
                    },
                    hoverinfo: 'text'
                });
            }

            Plotly.newPlot('chart', traces, {
                showlegend: colorBy !== 'funding',
                margin: { l: 40, r: 150, t: 20, b: 40 },
                xaxis: { showgrid: false },
                yaxis: { showgrid: false },
                hovermode: 'closest'
            }, { responsive: true });
        }

        function resetFilters() {
            document.getElementById('yearMin').value = 2000;
            document.getElementById('yearMax').value = 2024;
            document.getElementById('fundMin').value = 0;
            document.getElementById('fundMax').value = 50;
            document.getElementById('search').value = '';
            updateChart();
        }

        loadData();
    </script>
</body>
</html>
HTMLEOF

echo "✓ HTML file created"

# Upload to GCS
echo "[2/4] Uploading to GCS..."
gsutil cp "${LOCAL_DIR}/topic_map_hybrid.html" "${BUCKET}/topic_map_hybrid.html"
echo "✓ Uploaded to GCS"

# Set metadata
echo "[3/4] Setting metadata..."
gsutil setmeta -h "Content-Type:text/html" -h "Cache-Control:no-cache" "${BUCKET}/topic_map_hybrid.html"
echo "✓ Metadata set"

# Verify
echo "[4/4] Verifying deployment..."
FILE_INFO=$(gsutil ls -lh "${BUCKET}/topic_map_hybrid.html")
echo "✓ File verified"
echo ""
echo "$FILE_INFO"

echo ""
echo "============================================================"
echo "✓ DEPLOYMENT COMPLETE"
echo "============================================================"
echo ""
echo "View at:"
echo "https://storage.googleapis.com/od-cl-odss-conroyri-nih-embeddings/sample/topic_map_hybrid.html"
echo ""
echo "Features:"
echo "  • Color by: Topic, Institute, or Funding"
echo "  • Year Range: 2000-2024"
echo "  • Funding Range: $0-50M+"
echo "  • Search titles"
echo "  • Reset all filters"
echo ""
echo "Hard refresh: Ctrl+Shift+R (or Cmd+Shift+R on Mac)"
echo "============================================================"
