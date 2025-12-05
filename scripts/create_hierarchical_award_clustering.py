#!/usr/bin/env python3
import pandas as pd
import numpy as np
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score
from sklearn.feature_extraction.text import TfidfVectorizer
import json

print("="*70)
print("CREATING HIERARCHICAL AWARD CLUSTERING")
print("="*70)

print("\n[1/6] Loading award data...")
df = pd.read_csv('awards_from_transactions_clustered.csv')
print(f"Loaded {len(df):,} awards")

coords_2d = df[['umap_x', 'umap_y']].values

print("\n[2/6] Clustering Level 1: DOMAINS (15 clusters)...")
kmeans_domain = KMeans(n_clusters=15, random_state=42, n_init=20, max_iter=500)
df['domain'] = kmeans_domain.fit_predict(coords_2d)

silhouette_domain = silhouette_score(coords_2d, df['domain'], sample_size=10000)
print(f"   Domains: {df['domain'].nunique()}")
print(f"   Silhouette: {silhouette_domain:.4f}")

print("   Generating domain labels...")
domain_info = {}
for domain_id in sorted(df['domain'].unique()):
    domain_df = df[df['domain'] == domain_id]
    vec = TfidfVectorizer(max_features=3, stop_words='english', ngram_range=(1,2))
    titles = ' '.join(domain_df['PROJECT_TITLE'].dropna().head(200).tolist())
    try:
        vec.fit([titles])
        label = ' & '.join([k.title() for k in vec.get_feature_names_out()])
    except:
        label = f'Domain {domain_id}'
    domain_info[domain_id] = {
        'label': label,
        'n_awards': len(domain_df),
        'funding': domain_df['TOTAL_COST'].sum(),
        'centroid_x': domain_df['umap_x'].mean(),
        'centroid_y': domain_df['umap_y'].mean()
    }

df['domain_label'] = df['domain'].map(lambda x: domain_info[x]['label'])

print("\n[3/6] Clustering Level 2: TOPICS (4 per domain)...")
df['topic'] = -1
topic_id = 0
topic_info = {}

for domain_id in sorted(df['domain'].unique()):
    domain_mask = df['domain'] == domain_id
    domain_indices = df[domain_mask].index
    domain_coords = df.loc[domain_indices, ['umap_x', 'umap_y']].values
    n_topics = min(4, max(2, len(domain_indices) // 5000))
    
    if len(domain_indices) > 10:
        kmeans_topic = KMeans(n_clusters=n_topics, random_state=42, n_init=10)
        domain_topics = kmeans_topic.fit_predict(domain_coords)
        
        for local_topic in range(n_topics):
            local_mask = domain_topics == local_topic
            global_indices = domain_indices[local_mask]
            df.loc[global_indices, 'topic'] = topic_id
            topic_df = df.loc[global_indices]
            
            vec = TfidfVectorizer(max_features=3, stop_words='english', ngram_range=(1,2))
            titles = ' '.join(topic_df['PROJECT_TITLE'].dropna().head(100).tolist())
            try:
                vec.fit([titles])
                label = ' & '.join([k.title() for k in vec.get_feature_names_out()])
            except:
                label = f'Topic {topic_id}'
            
            topic_info[topic_id] = {
                'label': label,
                'domain': domain_id,
                'n_awards': len(topic_df),
                'funding': topic_df['TOTAL_COST'].sum(),
                'centroid_x': topic_df['umap_x'].mean(),
                'centroid_y': topic_df['umap_y'].mean()
            }
            topic_id += 1

print(f"   Total topics: {df['topic'].nunique()}")
df['topic_label'] = df['topic'].map(lambda x: topic_info.get(x, {}).get('label', f'Topic {x}'))

print("\n[4/6] Clustering Level 3: SUBTOPICS (3 per topic)...")
df['subtopic'] = -1
subtopic_id = 0
subtopic_info = {}

for tid in sorted([t for t in df['topic'].unique() if t != -1]):
    topic_mask = df['topic'] == tid
    topic_indices = df[topic_mask].index
    topic_coords = df.loc[topic_indices, ['umap_x', 'umap_y']].values
    n_subtopics = min(3, max(2, len(topic_indices) // 1000))
    
    if len(topic_indices) > 5:
        kmeans_subtopic = KMeans(n_clusters=n_subtopics, random_state=42, n_init=10)
        topic_subtopics = kmeans_subtopic.fit_predict(topic_coords)
        
        for local_subtopic in range(n_subtopics):
            local_mask = topic_subtopics == local_subtopic
            global_indices = topic_indices[local_mask]
            df.loc[global_indices, 'subtopic'] = subtopic_id
            subtopic_df = df.loc[global_indices]
            
            vec = TfidfVectorizer(max_features=3, stop_words='english', ngram_range=(1,2))
            titles = ' '.join(subtopic_df['PROJECT_TITLE'].dropna().head(50).tolist())
            try:
                vec.fit([titles])
                label = ' & '.join([k.title() for k in vec.get_feature_names_out()])
            except:
                label = f'Subtopic {subtopic_id}'
            
            subtopic_info[subtopic_id] = {
                'label': label,
                'topic': tid,
                'domain': topic_info[tid]['domain'],
                'n_awards': len(subtopic_df),
                'funding': subtopic_df['TOTAL_COST'].sum(),
                'centroid_x': subtopic_df['umap_x'].mean(),
                'centroid_y': subtopic_df['umap_y'].mean()
            }
            subtopic_id += 1

print(f"   Total subtopics: {df['subtopic'].nunique()}")
df['subtopic_label'] = df['subtopic'].map(lambda x: subtopic_info.get(x, {}).get('label', f'Subtopic {x}'))

print("\n[5/6] Saving...")
df.to_csv('awards_hierarchical_clustered.csv', index=False)
print("   Saved: awards_hierarchical_clustered.csv")

print("\n" + "="*70)
print(f"DOMAINS: {df['domain'].nunique()} | TOPICS: {df['topic'].nunique()} | SUBTOPICS: {df['subtopic'].nunique()}")
print(f"Total: {len(df):,} awards | ${df['TOTAL_COST'].sum()/1e9:.1f}B")
print("="*70)

print("\nTop 10 Domains:")
for domain_id in sorted(domain_info.keys(), key=lambda x: domain_info[x]['funding'], reverse=True)[:10]:
    info = domain_info[domain_id]
    print(f"D{domain_id:2d}: {info['label'][:45]:<45} | ${info['funding']/1e9:>5.1f}B")

print("\n[6/6] Creating interactive map...")

sample_size = min(50000, len(df))
df_viz = df.sample(n=sample_size, random_state=42) if len(df) > sample_size else df

viz_data = {
    'x': df_viz['umap_x'].tolist(),
    'y': df_viz['umap_y'].tolist(),
    'domain': df_viz['domain'].tolist(),
    'topic': df_viz['topic'].tolist(),
    'subtopic': df_viz['subtopic'].tolist(),
    'domain_label': df_viz['domain_label'].tolist(),
    'topic_label': df_viz['topic_label'].tolist(),
    'subtopic_label': df_viz['subtopic_label'].tolist(),
    'funding': df_viz['TOTAL_COST'].tolist(),
    'ic': df_viz['IC_NAME'].tolist(),
    'fy': df_viz['FY'].tolist(),
    'title': df_viz['PROJECT_TITLE'].tolist()
}

html = """<!DOCTYPE html><html><head><meta charset="UTF-8"><title>NIH Hierarchical Map</title>
<script src="https://cdn.plot.ly/plotly-2.27.0.min.js"></script>
<style>body{margin:0;padding:0;background:#0a0a0a;color:#fff;font-family:sans-serif}
.header{background:linear-gradient(135deg,#1a1a2e,#16213e);padding:30px;border-bottom:3px solid #0f3460}
h1{margin:0 0 10px 0;color:#eaeaea}select{background:#16213e;color:#a8dadc;border:1px solid #0f3460;
padding:8px 12px;border-radius:4px;cursor:pointer}#plotDiv{background:#0a0a0a}</style></head><body>
<div class="header"><h1>NIH Award Map: Hierarchical Clustering</h1>
<div style="color:#a8dadc;margin:15px 0">""" + f"{len(df):,} awards | {df['domain'].nunique()} domains → {df['topic'].nunique()} topics → {df['subtopic'].nunique()} subtopics | ${df['TOTAL_COST'].sum()/1e9:.1f}B" + """</div>
<label style="color:#81b7d2">View Level:</label>
<select id="levelSelect" onchange="updateView()">
<option value="domain">Domain (15)</option><option value="topic">Topic (~60)</option>
<option value="subtopic" selected>Subtopic (~180)</option></select></div>
<div id="plotDiv"></div><script>
const data=""" + json.dumps(viz_data) + """;
const domainInfo=""" + json.dumps({str(k): v for k, v in domain_info.items()}) + """;
const topicInfo=""" + json.dumps({str(k): v for k, v in topic_info.items()}) + """;
const subtopicInfo=""" + json.dumps({str(k): v for k, v in subtopic_info.items()}) + """;
let currentLevel='subtopic';
function updateView(){currentLevel=document.getElementById('levelSelect').value;createPlot();}
function createPlot(){let clusterData,clusterInfo,levelName;
if(currentLevel==='domain'){clusterData=data.domain;clusterInfo=domainInfo;levelName='Domain';}
else if(currentLevel==='topic'){clusterData=data.topic;clusterInfo=topicInfo;levelName='Topic';}
else{clusterData=data.subtopic;clusterInfo=subtopicInfo;levelName='Subtopic';}
const trace={x:data.x,y:data.y,mode:'markers',type:'scattergl',
marker:{size:3,color:clusterData,colorscale:'Viridis',showscale:true,
colorbar:{title:{text:levelName,font:{color:'#eaeaea'}},tickfont:{color:'#eaeaea'},thickness:20,len:0.7},
opacity:0.85,line:{width:0.3,color:'rgba(255,255,255,0.2)'}},
text:clusterData.map((c,i)=>'<b>'+levelName+' '+c+'</b><br>Domain: '+data.domain_label[i]+'<br>Topic: '+
data.topic_label[i]+'<br>Subtopic: '+data.subtopic_label[i]+'<br><br>IC: '+data.ic[i]+'<br>FY: '+data.fy[i]+
'<br>Funding: $'+(data.funding[i]/1e6).toFixed(1)+'M<br>Title: '+data.title[i].substring(0,60)+'...'),
hovertemplate:'<span style="color:#a8dadc">%{text}</span><extra></extra>'};
const annotations=[];Object.keys(clusterInfo).forEach(cid=>{const info=clusterInfo[cid];
if(info.n_awards>100){annotations.push({x:info.centroid_x,y:info.centroid_y,text:'<b>'+cid+'</b>',
showarrow:false,font:{size:currentLevel==='domain'?14:(currentLevel==='topic'?10:8),color:'white',
family:'Arial Black'},bgcolor:'rgba(15,52,96,0.9)',bordercolor:'#a8dadc',borderwidth:2,borderpad:4});}});
const layout={title:{text:'NIH Awards: '+levelName+' View',font:{size:20,color:'#eaeaea'}},
xaxis:{title:'UMAP 1',showgrid:false,zeroline:false,color:'#81b7d2'},
yaxis:{title:'UMAP 2',showgrid:false,zeroline:false,color:'#81b7d2'},
hovermode:'closest',height:900,plot_bgcolor:'#0a0a0a',paper_bgcolor:'#0a0a0a',annotations:annotations};
const config={responsive:true,displayModeBar:true,modeBarButtonsToRemove:['lasso2d','select2d'],displaylogo:false};
Plotly.newPlot('plotDiv',[trace],layout,config);}
createPlot();</script></body></html>"""

with open('award_map_hierarchical.html', 'w') as f:
    f.write(html)

print("   Saved: award_map_hierarchical.html")
print("\n" + "="*70)
print("COMPLETE! Open award_map_hierarchical.html")
print("="*70)
