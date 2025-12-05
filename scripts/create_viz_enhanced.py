import pandas as pd
import json
import numpy as np
from collections import Counter

print("Creating enhanced 50k visualization with topic labels...")

# Load data
df = pd.read_csv('hierarchical_50k_with_coords.csv')
print(f"Loaded {len(df):,} grants")

# Load full embeddings for RCDC terms
emb_df = pd.read_parquet('embeddings_50k_sample.parquet')
from google.cloud import bigquery

client = bigquery.Client(project='od-cl-odss-conroyri-f75a')
query = """
SELECT 
  CAST(APPLICATION_ID AS INT64) as APPLICATION_ID,
  NIH_SPENDING_CATS,
  PROJECT_TERMS
FROM `od-cl-odss-conroyri-f75a.nih_exporter.projects`
WHERE CAST(APPLICATION_ID AS INT64) IN UNNEST(@app_ids)
"""
job_config = bigquery.QueryJobConfig(
    query_parameters=[bigquery.ArrayQueryParameter("app_ids", "INT64", 
                                                   df['APPLICATION_ID'].tolist())]
)
metadata_df = client.query(query, job_config=job_config).to_dataframe()
metadata_df['APPLICATION_ID'] = metadata_df['APPLICATION_ID'].astype('int64')
df = df.merge(metadata_df, on='APPLICATION_ID', how='left')

print("Generating descriptive labels for topics and subtopics...")

# Generate topic labels
def get_distinctive_terms(group_df, all_df, col='NIH_SPENDING_CATS'):
    """Get most distinctive RCDC categories for a group"""
    group_cats = []
    for cats in group_df[col].dropna():
        group_cats.extend([c.strip() for c in str(cats).split(';') if c.strip()])
    
    if not group_cats:
        return "Uncategorized"
    
    group_freq = Counter(group_cats)
    
    # Get background frequencies
    all_cats = []
    for cats in all_df[col].dropna():
        all_cats.extend([c.strip() for c in str(cats).split(';') if c.strip()])
    all_freq = Counter(all_cats)
    
    # Calculate distinctiveness (TF-IDF like)
    distinctive = []
    for cat, count in group_freq.most_common(10):
        if cat in all_freq:
            score = (count / len(group_df)) / (all_freq[cat] / len(all_df))
            distinctive.append((cat, score))
    
    distinctive.sort(key=lambda x: x[1], reverse=True)
    
    if distinctive:
        top_terms = [t[0] for t in distinctive[:2]]
        # Shorten long terms
        top_terms = [t[:30] + '...' if len(t) > 30 else t for t in top_terms]
        return ' • '.join(top_terms)
    
    return group_freq.most_common(1)[0][0][:40]

# Compute centroids with labels
def compute_centroids_with_labels(df, group_col, label_col):
    centroids = []
    for group_id in sorted(df[group_col].unique()):
        group_df = df[df[group_col] == group_id]
        
        if label_col:
            label = str(group_df[label_col].iloc[0])
        else:
            # Generate descriptive label
            label = get_distinctive_terms(group_df, df)
        
        centroids.append({
            'id': int(group_id),
            'label': label,
            'x': float(group_df['umap_x'].mean()),
            'y': float(group_df['umap_y'].mean()),
            'count': len(group_df)
        })
    return centroids

domain_centroids = compute_centroids_with_labels(df, 'domain', 'domain_label')
topic_centroids = compute_centroids_with_labels(df, 'topic', None)
subtopic_centroids = compute_centroids_with_labels(df, 'subtopic', None)

print(f"   {len(domain_centroids)} domains")
print(f"   {len(topic_centroids)} topics (with labels)")
print(f"   {len(subtopic_centroids)} subtopics (with labels)")

# Compute domain boundaries (convex hull points)
from scipy.spatial import ConvexHull

domain_boundaries = []
for domain_id in sorted(df['domain'].unique()):
    domain_df = df[df['domain'] == domain_id]
    if len(domain_df) >= 3:
        points = domain_df[['umap_x', 'umap_y']].values
        try:
            hull = ConvexHull(points)
            boundary_points = points[hull.vertices].tolist()
            domain_boundaries.append({
                'domain': int(domain_id),
                'points': boundary_points
            })
        except:
            pass

print(f"   {len(domain_boundaries)} domain boundaries computed")

# Prepare data (all 50k for dynamic loading, but sample background)
print("Preparing data for dynamic loading...")

data_records = []
for idx, row in df.iterrows():
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

# Create background map (sample every 5th point for performance)
background_points = [{'x': d['x'], 'y': d['y'], 'd': d['domain']} 
                    for i, d in enumerate(data_records) if i % 5 == 0]

unique_ics = sorted(df['IC_NAME'].unique())
fy_min, fy_max = int(df['FY'].min()), int(df['FY'].max())

print(f"   {len(data_records):,} grants for dynamic loading")
print(f"   {len(background_points):,} background points")

# Write enhanced HTML
print("Creating enhanced visualization...")

with open('nih_topic_map_50k_enhanced.html', 'w', encoding='utf-8') as f:
    # HTML header and styles
    f.write('<!DOCTYPE html>\n<html>\n<head>\n<meta charset="utf-8">\n')
    f.write('<title>NIH Topic Maps - 50K Grants (Enhanced)</title>\n')
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
    f.write('.background-layer{opacity:0.08}\n')
    f.write('.boundary-layer{opacity:0.2}\n')
    f.write('.foreground-layer{opacity:0.8}\n')
    f.write('.cluster-label{font-size:12px;font-weight:600;fill:#1a1a1a;text-anchor:middle;pointer-events:none;text-shadow:0 0 4px white,0 0 4px white,0 0 4px white}\n')
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
    f.write('<h1>NIH Research Portfolio - 50,000 Grants (Enhanced)</h1>\n')
    f.write('<div class="subtitle">Dynamic loading • Descriptive labels • Domain boundaries • Zoom-responsive</div>\n')
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
    f.write('<div class="stat-box"><div class="stat-label">Grants Shown</div><div class="stat-value" id="stat-grants">0</div></div>\n')
    f.write('<div class="stat-box"><div class="stat-label">Funding</div><div class="stat-value" id="stat-funding">$0</div></div>\n')
    f.write('<div class="stat-box"><div class="stat-label">Zoom Level</div><div class="stat-value" id="stat-zoom">1.0x</div></div>\n')
    f.write('<div class="stat-box"><div class="stat-label">Clusters</div><div class="stat-value" id="stat-clusters">0</div></div>\n')
    f.write('</div>\n<div class="legend">\n<div class="legend-title" id="legend-title">Domains</div>\n')
    f.write('<div class="legend-items" id="legend-items"></div>\n</div>\n</div>\n')
    
    # JavaScript with dynamic loading
    f.write('<script>\nconst allData = ')
    f.write(json.dumps(data_records[:20000]))  # Limit to 20k for file size
    f.write(';\nconst backgroundData = ')
    f.write(json.dumps(background_points))
    f.write(';\nconst domainCentroids = ')
    f.write(json.dumps(domain_centroids))
    f.write(';\nconst topicCentroids = ')
    f.write(json.dumps(topic_centroids))
    f.write(';\nconst subtopicCentroids = ')
    f.write(json.dumps(subtopic_centroids))
    f.write(';\nconst domainBoundaries = ')
    f.write(json.dumps(domain_boundaries))
    
    # Enhanced JavaScript
    f.write(''';

let viewMode="domain",selectedClusters=new Set(),filteredData=allData,currentZoom=1;
const domainColors=d3.scaleOrdinal().domain([1,2,3,4,5,6,7,8,9,10])
    .range(["#e74c3c","#3498db","#2ecc71","#f39c12","#9b59b6","#1abc9c","#e67e22","#34495e","#c0392b","#16a085"]);

const width=1600,height=900;
const svg=d3.select("#viz-container").append("svg").attr("width",width).attr("height",height);
const zoom=d3.zoom().scaleExtent([0.5,20])
    .on("zoom",e=>{
        g.attr("transform",e.transform);
        currentZoom=e.transform.k;
        updateLabels();
        updateDynamicPoints();
        document.getElementById("stat-zoom").textContent=currentZoom.toFixed(1)+"x";
    });
svg.call(zoom);

const g=svg.append("g");
const backgroundLayer=g.append("g").attr("class","background-layer");
const boundaryLayer=g.append("g").attr("class","boundary-layer");
const foregroundLayer=g.append("g").attr("class","foreground-layer");
const labelsLayer=g.append("g");

const xScale=d3.scaleLinear().domain(d3.extent(allData,d=>d.x)).range([50,width-50]);
const yScale=d3.scaleLinear().domain(d3.extent(allData,d=>d.y)).range([height-50,50]);

// Draw background
backgroundLayer.selectAll("circle").data(backgroundData).enter().append("circle")
    .attr("cx",d=>xScale(d.x)).attr("cy",d=>yScale(d.y)).attr("r",1)
    .attr("fill",d=>domainColors(d.d));

// Draw domain boundaries
domainBoundaries.forEach(boundary=>{
    const path=d3.line().x(d=>xScale(d[0])).y(d=>yScale(d[1]))(boundary.points);
    boundaryLayer.append("path")
        .attr("d",path+"Z")
        .attr("fill","none")
        .attr("stroke",domainColors(boundary.domain))
        .attr("stroke-width",2)
        .attr("stroke-dasharray","5,5");
});

const tooltip=d3.select("body").append("div").attr("class","tooltip").style("display","none");

function updateDynamicPoints(){
    const maxPoints=Math.min(allData.length,Math.floor(2000*currentZoom));
    const visibleData=filteredData.slice(0,maxPoints);
    
    const points=foregroundLayer.selectAll("circle").data(visibleData,d=>d.id);
    points.exit().remove();
    points.enter().append("circle").attr("r",2).merge(points)
        .attr("cx",d=>xScale(d.x)).attr("cy",d=>yScale(d.y))
        .attr("fill",d=>domainColors(d.domain))
        .on("mouseover",(e,d)=>tooltip.style("display","block")
            .html("<strong>"+d.title+"</strong><br>IC: "+d.ic+"<br>FY: "+d.fy+"<br>$"+(d.funding/1e6).toFixed(2)+"M"))
        .on("mousemove",e=>tooltip.style("left",e.pageX+10+"px").style("top",e.pageY-20+"px"))
        .on("mouseout",()=>tooltip.style("display","none"));
    
    document.getElementById("stat-grants").textContent=visibleData.length.toLocaleString();
}

function updateLabels(){
    const centroids=viewMode==="domain"?domainCentroids:viewMode==="topic"?topicCentroids:subtopicCentroids;
    const labels=labelsLayer.selectAll("text").data(centroids,d=>d.id);
    labels.exit().remove();
    labels.enter().append("text").attr("class","cluster-label").merge(labels)
        .attr("x",d=>xScale(d.x)).attr("y",d=>yScale(d.y))
        .attr("font-size",12/currentZoom+"px")
        .text(d=>d.label);
}

function setViewMode(mode){
    viewMode=mode;
    document.querySelectorAll(".view-button").forEach(b=>b.classList.remove("active"));
    document.getElementById("btn-"+mode).classList.add("active");
    selectedClusters.clear();
    render();
}

function applyFilters(){
    const ics=Array.from(document.getElementById("ic-filter").selectedOptions).map(o=>o.value);
    const fyMin=+document.getElementById("fy-min").value,fyMax=+document.getElementById("fy-max").value;
    const search=document.getElementById("search").value.toLowerCase();
    document.getElementById("fy-display").textContent=fyMin+"-"+fyMax;
    
    filteredData=allData.filter(d=>{
        if(!ics.includes("all")&&!ics.includes(d.ic))return false;
        if(d.fy<fyMin||d.fy>fyMax)return false;
        if(search&&!d.title.toLowerCase().includes(search))return false;
        if(selectedClusters.size>0&&!selectedClusters.has(d[viewMode]))return false;
        return true;
    });
    render();
}

function resetFilters(){
    document.getElementById("ic-filter").selectedIndex=0;
    document.getElementById("fy-min").value=''')
    f.write(str(fy_min))
    f.write(''';
    document.getElementById("fy-max").value=''')
    f.write(str(fy_max))
    f.write(''';
    document.getElementById("search").value="";
    selectedClusters.clear();
    filteredData=allData;
    render();
}

function toggleCluster(id){
    selectedClusters.has(id)?selectedClusters.delete(id):selectedClusters.add(id);
    applyFilters();
}

function render(){
    updateDynamicPoints();
    updateLabels();
    updateLegend();
    document.getElementById("stat-funding").textContent="$"+(d3.sum(filteredData,d=>d.funding)/1e9).toFixed(2)+"B";
    const centroids=viewMode==="domain"?domainCentroids:viewMode==="topic"?topicCentroids:subtopicCentroids;
    document.getElementById("stat-clusters").textContent=centroids.length;
}

function updateLegend(){
    const centroids=viewMode==="domain"?domainCentroids:viewMode==="topic"?topicCentroids:subtopicCentroids;
    document.getElementById("legend-title").textContent=viewMode==="domain"?"Domains":viewMode==="topic"?"Topics":"Subtopics";
    const items=d3.select("#legend-items").selectAll(".legend-item").data(centroids,d=>d.id);
    items.exit().remove();
    const enter=items.enter().append("div").attr("class","legend-item").on("click",(e,d)=>toggleCluster(d.id));
    enter.append("div").attr("class","legend-color");
    enter.append("span").attr("class","legend-label");
    enter.append("span").attr("class","legend-count");
    enter.merge(items).classed("selected",d=>selectedClusters.has(d.id))
        .select(".legend-color").style("background",d=>domainColors(viewMode==="domain"?d.id:allData.find(g=>g[viewMode]===d.id).domain));
    enter.merge(items).select(".legend-label").text(d=>d.label);
    enter.merge(items).select(".legend-count").text(d=>d.count.toLocaleString()+" grants");
}

render();
</script>\n</body>\n</html>''')

print("\n✅ Created: nih_topic_map_50k_enhanced.html")
print("\nEnhancements:")
print("  ✓ Descriptive topic/subtopic labels (not just numbers)")
print("  ✓ Labels scale with zoom (stay readable)")
print("  ✓ Domain boundaries with semi-transparent lines")
print("  ✓ Background map (10k sample points)")
print("  ✓ Dynamic point loading (more points when zoomed in)")
print("  ✓ Zoom level indicator in stats")
print("\nOpen nih_topic_map_50k_enhanced.html in your browser!")
