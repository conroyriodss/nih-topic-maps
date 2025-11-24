from flask import Flask, render_template, request, redirect, session, jsonify
import os
import json
from google.cloud import storage

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'change-me-in-production')
PASSWORD = os.environ.get('SITE_PASSWORD', 'nih-topics-2024')

# Initialize GCS client
storage_client = storage.Client()
bucket_name = 'od-cl-odss-conroyri-nih-embeddings'

@app.route('/')
def index():
    if not session.get('authenticated'):
        return redirect('/login')
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        if request.form.get('password') == PASSWORD:
            session['authenticated'] = True
            return redirect('/')
        return 'Invalid password', 401
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('authenticated', None)
    return redirect('/login')

@app.route('/topics')
def topics():
    if not session.get('authenticated'):
        return redirect('/login')
    
    # Load topic info from GCS
    bucket = storage_client.bucket(bucket_name)
    blob = bucket.blob('sample/topic_info_final_75.json')
    topic_data = json.loads(blob.download_as_text())
    
    # Sort by size
    topics_list = sorted(
        [(int(k), v) for k, v in topic_data.items()],
        key=lambda x: x[1]['size'],
        reverse=True
    )
    
    return render_template('topics.html', topics=topics_list)

@app.route('/visualization')
def visualization():
    if not session.get('authenticated'):
        return redirect('/login')
    return render_template('visualization.html')

@app.route('/api/topics')
def api_topics():
    if not session.get('authenticated'):
        return jsonify({'error': 'Not authenticated'}), 401
    
    bucket = storage_client.bucket(bucket_name)
    blob = bucket.blob('sample/topic_info_final_75.json')
    topic_data = json.loads(blob.download_as_text())
    return jsonify(topic_data)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 8080)))
