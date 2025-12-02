import pandas as pd
import json
import numpy as np

print("Creating 50k interactive visualization...")

# Load data
df = pd.read_csv('hierarchical_50k_with_coords.csv')
print(f"Loaded {len(df):,} grants")

# Compute centroids
def compute_centroids(df, group_col, label_col):
    centroids = []
    for group_id in sorted(df[group_col].unique()):
        group_df = df[df[group_col] == group_id]
        centroids.append({
            'id': int(group_id),
            'label': str(group_df[label_col].iloc[0]) if label_col else f"Cluster {group_id}",
            'x': float(group_df['umap_x'].mean()),
            'y': float(group_df['umap_y'].mean()),
            'count': len(group_df)
        })
    return centroids

domain_centroids = compute_centroids(df, 'domain', 'domain_label')
topic_centroids = compute_centroids(df, 'topic', None)
subtopic_centroids = compute_centroids(df, 'subtopic', None)

for t in topic_centroids:
    t['label'] = f"Topic {t['id']}"
for s in subtopic_centroids:
    s['label'] = f"Sub {s['id']}"

# Prepare data (use 10k subset for file size)
data_records = []
for idx, row in df.head(10000).iterrows():
    data_records.append({
        'id': str(row['APPLICATION_ID']),
        'title': str(row['PROJECT_TITLE'])[:150],
        'ic': str(row['IC_NAME'])[:50],
        'fy': int(row['FY']),
        'funding': float(row['TOTAL_COST']) if pd.notna(row['TOTAL_COST']) else 0,
        'domain': int(row['domain']),
        'topic': int(row['topic']),
        'subtopic': int(row['subtopic']),
        'x': float(row['umap_x']),
        'y': float(row['umap_y'])
    })

background_points = [{'x': d['x'], 'y': d['y'], 'd': d['domain']} for d in data_records]
unique_ics = sorted(df['IC_NAME'].unique())
fy_min, fy_max = int(df['FY'].min()), int(df['FY'].max())

print(f"Prepared {len(data_records):,} grants for visualization")

# Write HTML file
with open('nih_topic_map_50k.html', 'w', encoding='utf-8') as f:
    # HTML header
    f.write('<!DOCTYPE html>\n<html>\n<head>\n<meta charset="utf-8">\n')
    f.write('<title>NIH Topic Maps - 50K Grants</title>\n')
    f.write('<script src="https://d3js.org/d3.v7.min.js"></script>\n')
    f.write('<style>\n')
    f.write('body{font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Arial,sans-serif;margin:0;padding:15px;background:#f5f5f5}\n')
    f.write('#container{max-width:1900px;margin:0 auto;background:white;border-radius:8px;box-shadow:0 2px 8px rgba(0,0,0,0.1);padding:15px}\n')
    f.write('h1{margin:0 0 5px 0;color:#1a1a1a;font-size:24px}\n')
    f.write('.subtitle{color:#666;margin-bottom:10px;font-size:12px}\n')
    f.write('.view-mode{display:flex;gap:8px;margin-bottom:10px}\n')
    f.write('.view-button{flex:1;padding:8px;background:#e0e0e0;border:none;border-radius:4px;cursor:pointer;font-size:12px;font-weight:600}\n')
    f.write('.view-button.active{background:#2196F3;color:white}\n')
    f.write('#controls{display:grid;grid-template-columns:repeat(auto-fit,minmax(250px,1fr));gap:12px;margin-bottom:12px;padding:12px;background:#f8f9fa;border-radius:6px}\n')
    f.write('.control-group{display:flex;flex-direction:column;gap:5px}\n')
    f.write('label{font-size:12px;font-weight:600;color:#444}\n')
    f.write('select,input,button{padding:6px 8px;border:1px solid #ddd;border-radius:4px;font-size:12px}\n')
    f.write('select[multiple]{height:80px}\n')
    f.write('button{background:#2196F3;color:white;border:none;cursor:pointer;padding:8px 16px;font-weight:600}\n')
    f.write('button:hover{background:#1976D2}\n')
    f.write('#viz-container{position:relative;border:1px solid #e0e0e0;border-radius:4px;background:#fafafa}\n')
    f.write('.background-layer{opacity:0.12}\n')
    f.write('.foreground-layer{opacity:0.8}\n')
    f.write('.cluster-label{font-size:11px;font-weight:600;fill:#1a1a1a;text-anchor:middle;pointer-events:none;text-shadow:0 0 3px white}\n')
    f.write('.tooltip{position:absolute;padding:10px;background:rgba(0,0,0,0.9);color:white;border-radius:4px;pointer-events:none;font-size:11px;max-width:300px;z-index:1000;line-height:1.4}\n')
    f.write('.tooltip strong{color:#4fc3f7}\n')
    f.write('.stats{display:grid;grid-template-columns:repeat(auto-fit,minmax(180px,1fr));gap:10px;margin-top:12px}\n')
    f.write('.stat-box{background:#f8f9fa;padding:12px;border-radius:4px;border-left:3px solid #2196F3}\n')
    f.write('.stat-label{font-size:11px;color:#666;margin-bottom:4px}\n')
    f.write('.stat-value{font-size:20px;font-weight:600;color:#1a1a1a}\n')
    f.write('.legend{margin-top:15px;padding:12px;background:#f8f9fa;border-radius:6px;max-height:400px;overflow-y:auto}\n')
    f.write('.legend-title{font-weight:600;margin-bottom:8px;color:#1a1a1a;font-size:13px}\n')
    f.write('.legend-items{display:grid;grid-template-columns:repeat(auto-fill,minmax(350px,1fr));gap:5px}\n')
    f.write('.legend-item{display:flex;align-items:center;gap:8px;font-size:11px;padding:5px;cursor:pointer;border-radius:3px;transition:background 0.2s}\n')
    f.write('.legend-item:hover{background:#e3f2fd}\n')
    f.write('.legend-item.selected{background:#bbdefb;font-weight:600}\n')
    f.write('.legend-color{width:14px;height:14px;border-radius:2px;flex-shrink:0}\n')
    f.write('.legend-count{margin-left:auto;color:#666;font-size:10px}\n')
    f.write('</style>\n</head>\n<body>\n')
    
    # HTML body
    f.write('<div id="container">\n')
    f.write('<h1>NIH Research Portfolio - 50,000 Grants</h1>\n')
    f.write('<div class="subtitle">10,000 grants shown • 10 domains, 60 topics, 239 subtopics</div>\n')
    f.write('<div class="view-mode">\n')
    f.write('<button class="view-button active" id="btn-domain" onclick="setViewMode(\'domain\')">Domain View</button>\n')
    f.write('<button class="view-button" id="btn-topic" onclick="setViewMode(\'topic\')">Topic View</button>\n')
    f.write('<button class="view-button" id="btn-subtopic" onclick="setViewMode(\'subtopic\')">Subtopic View</button>\n')
    f.write('</div>\n<div id="controls">\n<div class="control-group">\n')
    f.write('<label>Institute/Center:</label>\n<select id="ic-filter" multiple>\n<option value="all" selected>All ICs</option>\n')
    
    for ic in unique_ics:
        f.write(f'<option value="{ic}">{ic[:50]}</option>\n')
    
    f.write(f'</select>\n</div>\n<div class="control-group">\n<label>Fiscal Year: <span id="fy-display">{fy_min}-{fy_max}</span></label>\n')
    f.write(f'<input type="range" id="fy-min" min="{fy_min}" max="{fy_max}" value="{fy_min}">\n')
    f.write(f'<input type="range" id="fy-max" min="{fy_min}" max="{fy_max}" value="{fy_max}">\n')
    f.write('</div>\n<div class="control-group">\n<label>Search:</label>\n')
    f.write('<input type="text" id="search" placeholder="Keywords...">\n</div>\n')
    f.write('<div class="control-group">\n<button onclick="applyFilters()">Apply</button>\n')
    f.write('<button onclick="resetFilters()" style="background:#757575">Reset</button>\n</div>\n</div>\n')
    f.write('<div id="viz-container"></div>\n<div class="stats">\n')
    f.write('<div class="stat-box"><div class="stat-label">Grants</div><div class="stat-value" id="stat-grants">0</div></div>\n')
    f.write('<div class="stat-box"><div class="stat-label">Funding</div><div class="stat-value" id="stat-funding">$0</div></div>\n')
    f.write('<div class="stat-box"><div class="stat-label">ICs</div><div class="stat-value" id="stat-ics">0</div></div>\n')
    f.write('<div class="stat-box"><div class="stat-label">Clusters</div><div class="stat-value" id="stat-clusters">0</div></div>\n')
    f.write('</div>\n<div class="legend">\n<div class="legend-title" id="legend-title">Domains</div>\n')
    f.write('<div class="legend-items" id="legend-items"></div>\n</div>\n</div>\n')
    
    # JavaScript
    f.write('<script>\nconst allData = ')
    f.write(json.dumps(data_records))
    f.write(';\nconst backgroundData = ')
    f.write(json.dumps(background_points))
    f.write(';\nconst domainCentroids = ')
    f.write(json.dumps(domain_centroids))
    f.write(';\nconst topicCentroids = ')
    f.write(json.dumps(topic_centroids))
    f.write(';\nconst subtopicCentroids = ')
    f.write(json.dumps(subtopic_centroids))
    f.write(';\n\nlet viewMode="domain",selectedClusters=new Set(),filteredData=allData;\n')
    f.write('const domainColors=d3.scaleOrdinal().domain([1,2,3,4,5,6,7,8,9,10]).range(["#e74c3c","#3498db","#2ecc71","#f39c12","#9b59b6","#1abc9c","#e67e22","#34495e","#c0392b","#16a085"]);\n')
    f.write('const width=1600,height=900;\n')
    f.write('const svg=d3.select("#viz-container").append("svg").attr("width",width).attr("height",height);\n')
    f.write('const zoom=d3.zoom().scaleExtent([0.5,20]).on("zoom",e=>g.attr("transform",e.transform));\n')
    f.write('svg.call(zoom);\nconst g=svg.append("g");\n')
    f.write('const backgroundLayer=g.append("g").attr("class","background-layer");\n')
    f.write('const foregroundLayer=g.append("g").attr("class","foreground-layer");\n')
    f.write('const labelsLayer=g.append("g");\n')
    f.write('const xScale=d3.scaleLinear().domain(d3.extent(allData,d=>d.x)).range([50,width-50]);\n')
    f.write('const yScale=d3.scaleLinear().domain(d3.extent(allData,d=>d.y)).range([height-50,50]);\n')
    f.write('backgroundLayer.selectAll("circle").data(backgroundData).enter().append("circle").attr("cx",d=>xScale(d.x)).attr("cy",d=>yScale(d.y)).attr("r",1.5).attr("fill",d=>domainColors(d.d));\n')
    f.write('const tooltip=d3.select("body").append("div").attr("class","tooltip").style("display","none");\n')
    f.write('function setViewMode(mode){viewMode=mode;document.querySelectorAll(".view-button").forEach(b=>b.classList.remove("active"));document.getElementById("btn-"+mode).classList.add("active");selectedClusters.clear();render();}\n')
    f.write('function applyFilters(){const ics=Array.from(document.getElementById("ic-filter").selectedOptions).map(o=>o.value);const fyMin=+document.getElementById("fy-min").value,fyMax=+document.getElementById("fy-max").value;const search=document.getElementById("search").value.toLowerCase();document.getElementById("fy-display").textContent=fyMin+"-"+fyMax;filteredData=allData.filter(d=>{if(!ics.includes("all")&&!ics.includes(d.ic))return false;if(d.fy<fyMin||d.fy>fyMax)return false;if(search&&!d.title.toLowerCase().includes(search))return false;if(selectedClusters.size>0&&!selectedClusters.has(d[viewMode]))return false;return true;});render();}\n')
    f.write(f'function resetFilters(){{document.getElementById("ic-filter").selectedIndex=0;document.getElementById("fy-min").value={fy_min};document.getElementById("fy-max").value={fy_max};document.getElementById("search").value="";selectedClusters.clear();filteredData=allData;render();}}\n')
    f.write('function toggleCluster(id){selectedClusters.has(id)?selectedClusters.delete(id):selectedClusters.add(id);applyFilters();}\n')
    f.write('function render(){const points=foregroundLayer.selectAll("circle").data(filteredData,d=>d.id);points.exit().remove();points.enter().append("circle").attr("r",2).merge(points).attr("cx",d=>xScale(d.x)).attr("cy",d=>yScale(d.y)).attr("fill",d=>domainColors(d.domain)).on("mouseover",(e,d)=>tooltip.style("display","block").html("<strong>"+d.title+"</strong><br>IC: "+d.ic+"<br>FY: "+d.fy+"<br>$"+(d.funding/1e6).toFixed(2)+"M")).on("mousemove",e=>tooltip.style("left",e.pageX+10+"px").style("top",e.pageY-20+"px")).on("mouseout",()=>tooltip.style("display","none"));const centroids=viewMode==="domain"?domainCentroids:viewMode==="topic"?topicCentroids:subtopicCentroids;const labels=labelsLayer.selectAll("text").data(centroids,d=>d.id);labels.exit().remove();labels.enter().append("text").attr("class","cluster-label").merge(labels).attr("x",d=>xScale(d.x)).attr("y",d=>yScale(d.y)).text(d=>viewMode==="domain"?d.label:"#"+d.id);updateLegend(centroids);document.getElementById("stat-grants").textContent=filteredData.length.toLocaleString();document.getElementById("stat-funding").textContent="$"+(d3.sum(filteredData,d=>d.funding)/1e9).toFixed(2)+"B";document.getElementById("stat-ics").textContent=new Set(filteredData.map(d=>d.ic)).size;document.getElementById("stat-clusters").textContent=new Set(filteredData.map(d=>d[viewMode])).size;}\n')
    f.write('function updateLegend(centroids){document.getElementById("legend-title").textContent=viewMode==="domain"?"Domains":viewMode==="topic"?"Topics":"Subtopics";const items=d3.select("#legend-items").selectAll(".legend-item").data(centroids,d=>d.id);items.exit().remove();const enter=items.enter().append("div").attr("class","legend-item").on("click",(e,d)=>toggleCluster(d.id));enter.append("div").attr("class","legend-color");enter.append("span").attr("class","legend-label");enter.append("span").attr("class","legend-count");enter.merge(items).classed("selected",d=>selectedClusters.has(d.id)).select(".legend-color").style("background",d=>domainColors(viewMode==="domain"?d.id:allData.find(g=>g[viewMode]===d.id).domain));enter.merge(items).select(".legend-label").text(d=>d.label);enter.merge(items).select(".legend-count").text(d=>d.count.toLocaleString()+" grants");}\n')
    f.write('render();\n</script>\n</body>\n</html>')

print("\n✅ Created: nih_topic_map_50k.html")
print("Open this file in your web browser!")
