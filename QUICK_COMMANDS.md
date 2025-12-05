Quick Commands Reference

Check Status
- Python jobs: ps aux | grep python
- Git status: git status
- Recent commits: git log --oneline -5
- Disk usage: du -sh data/processed/

Visualization URLs
- Comparison: https://storage.googleapis.com/od-cl-odss-conroyri-nih-embeddings/sample/compare_umap_simple.html
- Interactive: https://storage.googleapis.com/od-cl-odss-conroyri-nih-embeddings/sample/project_terms_interactive.html
- TF-IDF (when ready): gs://od-cl-odss-conroyri-nih-embeddings/sample/viz_tfidf_filtered.json

Upload to GCS
gsutil cp FILE gs://od-cl-odss-conroyri-nih-embeddings/sample/

Check TF-IDF Results
ls -lh data/processed/viz_tfidf_filtered.json

Files to Clean Up (Old)
- create_full_viz*.html
- hosted_current.html
- test_viz.html
- topic_map_*.html

Archive old files:
mkdir -p archive
mv create_full_viz*.html hosted_current.html test_viz.html topic_map_*.html archive/
