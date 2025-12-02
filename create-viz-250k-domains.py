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

# Prepare data - sample to 50K for performance
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

print(f"   {len(data_records):,} grants in visualization")

# Write HTML
print("Creating HTML...")
with open('nih_topic_map_250k_domains.html', 'w', encoding='utf-8') as f:
    f.write('<!DOCTYPE html>\n<html>\n<head>\n<meta charset="utf-8">\n')
    f.write('<title>NIH Topic Maps - 250K Grants</title>\n')
    f.write('<script src="https://d3js.org/d3.v7.min.js"></script>\n')
    f.write('<style>\n')
    f.write('body{font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Arial,sans-serif;margin:0;padding:15px;background:#f5f5f5}\n')
    f.write('#container{max-width:1900px;margin:0 auto;background:white;border-radius:8px;box-shadow:0 2px 8px rgba(0,0,0,0.1);padding:15px}\n')
    f.write('h1{margin:0 0 5px 0;color:#1a1a1a;font-size:24px}\n')
    f.write('.subtitle{color:#666;margin-bottom:10px;font-size:12px}\n')
    f.write('#controls{display:grid;grid-template-columns:repeat(auto-fit,minmax(250px,1fr));gap:12px;margin-bottom:12px;padding:12px;background:#f8f9fa;border-radius:6px}\n')
    f.write('.control-group{display:flex;flex-direction:column;gap:5px}\n')
    f.write('label{font-size:12px;font-weight:600;color:#444}\n')
    f.write('select,input,button{padding:6px 8px;border:1px solid #ddd;border-radius:4px;font-size:12px}\n')
    f.write('select[multiple]{height:80px}\n')
    f.write('button{background:#2196F3;color:white;border:none;cursor:pointer;padding:8px 16px;font-weight:600}\n')
    f.write('button:hover{background:#1976D2}\n')
    f.write('#viz-container{position:relative;border:1px solid #e0e0e0;border-radius:4px;background:#fafafa}\n')
    f.write('.heatmap-layer{opacity:0.3}\n')
    f.write('.background-layer{opacity:0.05}\n')
    f.write('.foreground-layer{opacity:0.8}\n')
    f.write('.cluster-label{font-size:14px;font-weight:600;fill:#1a1a1a;text-anchor:middle;pointer-events:none;text-shadow:0 0 4px white,0 0 4px white,0 0 4px white}\n')
    f.write('.award-card{position:absolute;background:rgba(255,255,255,0.98);border:2px solid #2196F3;border-radius:8px;padding:12px;max-width:400px;box-shadow:0 4px 12px rgba(0,0,0,0.2);z-index:2000;font-size:12px;line-height:1.4}\n')
    f.write('.award-card-header{font-weight:700;font-size:14px;color:#1a1a1a;margin-bottom:8px;border-bottom:2px solid #2196F3;padding-bottom:6px}\n')
    f.write('.award-item{margin-bottom:10px;padding:8px;background:#f8f9fa;border-radius:4px;border-left:3px solid #4caf50}\n')
    f.write('.award-title{font-weight:600;color:#1a1a1a;margin-bottom:4px;word-wrap:break-word;white-space:normal}\n')
    f.write('.award-meta{font-size:11px;color:#666;display:grid;grid-template-columns:1fr 1fr;gap:4px;margin-top:4px}\n')
    f.write('.award-total{margin-top:8px;padding-top:8px;border-top:2px solid #ddd;font-size:13px;font-weight:700;color:#2196F3}\n')
    f.write('.award-close{position:absolute;top:8px;right:8px;cursor:pointer;font-size:18px;color:#999;font-weight:700}\n')
    f.write('.award-close:hover{color:#f44336}\n')
    f.write('.tooltip{position:absolute;padding:10px;background:rgba(0,0,0,0.9);color:white;border-radius:4px;pointer-events:none;font-size:11px;max-width:350px;z-index:1000;line-height:1.4}\n')
    f.write('.tooltip strong{color:#4fc3f7}\n')
    f.write('.stats{display:grid;grid-template-columns:repeat(auto-fit,minmax(180px,1fr));gap:10px;margin-top:12px}\n')
    f.write('.stat-box{background:#f8f9fa;padding:12px;border-radius:4px;border-left:3px solid #2196F3}\n')
    f.write('.stat-label{font-size:11px;color:#666;margin-bottom:4px}\n')
    f.write('.stat-value{font-size:20px;font-weight:600;color:#1a1a1a}\n')
    f.write('.legend{margin-top:15px;padding:12px;background:#f8f9fa;border-radius:6px}\n')
    f.write('.legend-title{font-weight:600;margin-bottom:8px;color:#1a1a1a;font-size:13px}\n')
    f.write('.legend-items{display:grid;grid-template-columns:repeat(auto-fill,minmax(400px,1fr));gap:5px}\n')
    f.write('.legend-item{display:flex;align-items:center;gap:8px;font-size:11px;padding:5px;cursor:pointer;border-radius:3px;transition:background 0.2s}\n')
    f.write('.legend-item:hover{background:#e3f2fd}\n')
    f.write('.legend-item.selected{background:#bbdefb;font-weight:600}\n')
    f.write('.legend-color{width:14px;height:14px;border-radius:2px;flex-shrink:0}\n')
    f.write('.legend-count{margin-left:auto;color:#666;font-size:10px}\n')
    f.write('</style>\n</head>\n<body>\n')
    
    f.write('<div id="container">\n')
    f.write('<h1>NIH Research Portfolio - 250K Grants</h1>\n')
    f.write('<div class="subtitle">Domain heatmaps • Full labels • Award cards • Click grants for details</div>\n')
    f.write('<div id="controls">\n<div class="control-group">\n')
    f.write('<label>Institute/Center:</label>\n<select id="ic-filter" multiple>\n<option value="all" selected>All ICs</option>\n')
    
    for ic in unique_ics:
        f.write(f'<option value="{ic}">{ic}</option>\n')
    
    f.write(f'</select>\n</div>\n<div class="control-group">\n<label>Fiscal Year: <span id="fy-display">{fy_min}-{fy_max}</span></label>\n')
    f.write(f'<input type="range" id="fy-min" min="{fy_min}" max="{fy_max}" value="{fy_min}">\n')
    f.write(f'<input type="range" id="fy-max" min="{fy_min}" max="{fy_max}" value="{fy_max}">\n')
    f.write('</div>\n<div class="control-group">\n<label>Search:</label>\n')
    f.write('<input type="text" id="search" placeholder="Keywords...">\n</div>\n')
    f.write('<div class="control-group">\n<button onclick="applyFilters()">Apply</button>\n')
    f.write('<button onclick="resetFilters()" style="background:#757575">Reset</button>\n</div>\n</div>\n')
    f.write('<div id="viz-container"></div>\n')
    f.write('<div id="award-cards"></div>\n')
    f.write('<div class="stats">\n')
    f.write('<div class="stat-box"><div class="stat-label">Total Grants</div><div class="stat-value">250,000</div></div>\n')
    f.write('<div class="stat-box"><div class="stat-label">Shown</div><div class="stat-value" id="stat-grants">0</div></div>\n')
    f.write('<div class="stat-box"><div class="stat-label">Funding</div><div class="stat-value" id="stat-funding">$0</div></div>\n')
    f.write('<div class="stat-box"><div class="stat-label">Zoom</div><div class="stat-value" id="stat-zoom">1.0x</div></div>\n')
    f.write('</div>\n<div class="legend">\n<div class="legend-title">Research Domains</div>\n')
    f.write('<div class="legend-items" id="legend-items"></div>\n</div>\n</div>\n')
    
    # Embed data
    f.write('<script>\n')
    f.write('const allData = ')
    f.write(json.dumps(data_records))
    f.write(';\n')
    f.write('const backgroundData = ')
    f.write(json.dumps(background_points))
    f.write(';\n')
    f.write('const heatmapData = ')
    f.write(json.dumps(heatmap_data))
    f.write(';\n')
    f.write('const domainCentroids = ')
    f.write(json.dumps(domain_centroids))
    f.write(';\n\n')
    
    # JavaScript (same as before but simpler - domain only)
    f.write('''let selectedDomains=new Set(),filteredData=allData,currentZoom=1;
const domainColors=d3.scaleOrdinal().domain([1,2,3,4,5,6,7,8,9,10])
    .range(["#e74c3c","#3498db","#2ecc71","#f39c12","#9b59b6","#1abc9c","#e67e22","#34495e","#c0392b","#16a085"]);

const width=1600,height=900;
const svg=d3.select("#viz-container").append("svg").attr("width",width).attr("height",height);
const zoom=d3.zoom().scaleExtent([0.5,20])
    .on("zoom",e=>{
        g.attr("transform",e.transform);
        currentZoom=e.transform.k;
        updateLabels();
        updatePoints();
        document.getElementById("stat-zoom").textContent=currentZoom.toFixed(1)+"x";
    });
svg.call(zoom);

const g=svg.append("g");
const heatmapLayer=g.append("g").attr("class","heatmap-layer");
const backgroundLayer=g.append("g").attr("class","background-layer");
const foregroundLayer=g.append("g").attr("class","foreground-layer");
const labelsLayer=g.append("g");

const xScale=d3.scaleLinear().domain(d3.extent(allData,d=>d.x)).range([50,width-50]);
const yScale=d3.scaleLinear().domain(d3.extent(allData,d=>d.y)).range([height-50,50]);

heatmapData.forEach(cell=>{
    heatmapLayer.append("rect")
        .attr("x",xScale(cell.x)-10).attr("y",yScale(cell.y)-10)
        .attr("width",20).attr("height",20)
        .attr("fill",domainColors(cell.domain))
        .attr("opacity",cell.intensity*0.4);
});

backgroundLayer.selectAll("circle").data(backgroundData).enter().append("circle")
    .attr("cx",d=>xScale(d.x)).attr("cy",d=>yScale(d.y)).attr("r",1)
    .attr("fill",d=>domainColors(d.d));

const tooltip=d3.select("body").append("div").attr("class","tooltip").style("display","none");

function showAwardCard(grant){
    const nearby=filteredData.filter(d=>Math.abs(d.x-grant.x)<0.5&&Math.abs(d.y-grant.y)<0.5).slice(0,5);
    const totalFunding=d3.sum(nearby,d=>d.funding);
    
    let html='<div class="award-card">';
    html+='<span class="award-close" onclick="closeAwardCard()">×</span>';
    html+='<div class="award-card-header">'+nearby.length+' Grant'+(nearby.length>1?'s':'')+'</div>';
    
    nearby.forEach(d=>{
        html+='<div class="award-item">';
        html+='<div class="award-title">'+d.title+'</div>';
        html+='<div class="award-meta">';
        html+='<div>IC: '+d.ic+'</div><div>FY: '+d.fy+'</div>';
        html+='<div>$'+(d.funding/1e6).toFixed(2)+'M</div><div>'+d.id+'</div>';
        html+='</div></div>';
    });
    
    html+='<div class="award-total">Total: $'+(totalFunding/1e6).toFixed(2)+'M</div></div>';
    document.getElementById("award-cards").innerHTML=html;
}

function closeAwardCard(){document.getElementById("award-cards").innerHTML='';}

function updatePoints(){
    const maxPoints=Math.min(filteredData.length,Math.floor(3000*currentZoom));
    const visibleData=filteredData.slice(0,maxPoints);
    
    const points=foregroundLayer.selectAll("circle").data(visibleData,d=>d.id);
    points.exit().remove();
    points.enter().append("circle").attr("r",2.5).merge(points)
        .attr("cx",d=>xScale(d.x)).attr("cy",d=>yScale(d.y))
        .attr("fill",d=>domainColors(d.domain))
        .attr("cursor","pointer")
        .on("click",(e,d)=>showAwardCard(d))
        .on("mouseover",(e,d)=>tooltip.style("display","block")
            .html("<strong>Click for details</strong><br>"+d.title.substring(0,100)+"..."))
        .on("mousemove",e=>tooltip.style("left",e.pageX+10+"px").style("top",e.pageY-20+"px"))
        .on("mouseout",()=>tooltip.style("display","none"));
    
    document.getElementById("stat-grants").textContent=visibleData.length.toLocaleString();
}

function updateLabels(){
    const labels=labelsLayer.selectAll("text").data(domainCentroids,d=>d.id);
    labels.exit().remove();
    labels.enter().append("text").attr("class","cluster-label").merge(labels)
        .attr("x",d=>xScale(d.x)).attr("y",d=>yScale(d.y))
        .attr("font-size",14/currentZoom+"px")
        .text(d=>d.label);
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
        if(selectedDomains.size>0&&!selectedDomains.has(d.domain))return false;
        return true;
    });
    render();
}

function resetFilters(){
    document.getElementById("ic-filter").selectedIndex=0;
    document.getElementById("fy-min").value=''' + str(fy_min) + ''';
    document.getElementById("fy-max").value=''' + str(fy_max) + ''';
    document.getElementById("search").value="";
    selectedDomains.clear();
    filteredData=allData;
    closeAwardCard();
    render();
}

function toggleDomain(id){
    selectedDomains.has(id)?selectedDomains.delete(id):selectedDomains.add(id);
    applyFilters();
}

function render(){
    updatePoints();
    updateLabels();
    updateLegend();
    document.getElementById("stat-funding").textContent="$"+(d3.sum(filteredData,d=>d.funding)/1e9).toFixed(2)+"B";
}

function updateLegend(){
    const items=d3.select("#legend-items").selectAll(".legend-item").data(domainCentroids,d=>d.id);
    items.exit().remove();
    const enter=items.enter().append("div").attr("class","legend-item").on("click",(e,d)=>toggleDomain(d.id));
    enter.append("div").attr("class","legend-color");
    enter.append("span").attr("class","legend-label");
    enter.append("span").attr("class","legend-count");
    enter.merge(items).classed("selected",d=>selectedDomains.has(d.id))
        .select(".legend-color").style("background",d=>domainColors(d.id));
    enter.merge(items).select(".legend-label").text(d=>d.label);
    enter.merge(items).select(".legend-count").text(d=>d.count.toLocaleString());
}

render();
</script>
</body>
</html>''')

print("\n✅ Created: nih_topic_map_250k_domains.html")
print("  • 250K grants (50K sample displayed)")
print("  • 10 research domains")
print("  • Domain heatmaps")
print("  • Award cards with grouping")
print("\nOpen in browser!")
