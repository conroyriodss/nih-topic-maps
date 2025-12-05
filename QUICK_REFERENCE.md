NIH Topic Maps - Quick Reference

GPU Pipeline Commands

Launch GPU VM and run embeddings (full pipeline):
  bash run_gpu_pipeline.sh

Monitor progress:
  bash monitor_gpu_vm.sh

Check results and cleanup:
  bash check_results_and_cleanup.sh

Emergency stop:
  bash emergency_stop_vm.sh

Fix dependencies if job failed:
  bash fix_and_restart_vm.sh

Manual VM Commands

SSH to VM:
  gcloud compute ssh nih-embeddings-gpu-vm --zone=us-central1-a

Check GPU:
  gcloud compute ssh nih-embeddings-gpu-vm --zone=us-central1-a --command='nvidia-smi'

View log:
  gcloud compute ssh nih-embeddings-gpu-vm --zone=us-central1-a --command='tail -f ~/embedding.log'

Delete VM:
  gcloud compute instances delete nih-embeddings-gpu-vm --zone=us-central1-a

After Embeddings Complete

Cluster with K=100:
  python3 scripts/06_cluster_project_terms.py --k 100

Compare clustering methods:
  python3 scripts/compare_clustering_methods.py

Generate UMAP visualization:
  python3 scripts/07_create_umap_project_terms.py --k 100

Repository Verification

Verify all files present:
  bash verify_repository.sh

Update documentation:
  git add CONTEXT_FOR_NEXT_SESSION.md
  git commit -m "Session update"
  git push origin master

GCS Commands

List embeddings:
  gsutil ls -lh gs://od-cl-odss-conroyri-nih-embeddings/sample/

Download embeddings:
  gsutil cp gs://od-cl-odss-conroyri-nih-embeddings/sample/embeddings_project_terms_50k.parquet data/processed/

Upload results:
  gsutil cp data/processed/*.parquet gs://od-cl-odss-conroyri-nih-embeddings/sample/

Cost Tracking

Check current costs:
  gcloud billing accounts list
  gcloud billing projects describe od-cl-odss-conroyri-f75a

Expected costs:
- GPU VM: $0.50/hour
- This job: $0.25-0.50 total (15-30 min)

Troubleshooting

Dependencies not installed:
  bash fix_and_restart_vm.sh

GPU not detected:
  gcloud compute ssh nih-embeddings-gpu-vm --zone=us-central1-a --command='nvidia-smi'

Job not running:
  gcloud compute ssh nih-embeddings-gpu-vm --zone=us-central1-a --command='ps aux | grep python'

Check for errors:
  gcloud compute ssh nih-embeddings-gpu-vm --zone=us-central1-a --command='tail -100 ~/embedding.log'

File Locations

Local (Cloud Shell):
- Scripts: ~/nih-topic-maps/scripts/
- Data: ~/nih-topic-maps/data/processed/
- Docs: ~/nih-topic-maps/docs/

Remote (GCS):
- Embeddings: gs://od-cl-odss-conroyri-nih-embeddings/sample/
- Visualizations: gs://od-cl-odss-conroyri-nih-embeddings/sample/

K Optimization Results (Nov 26)

Best K values tested:
- K=50: Silhouette 0.022 (best metric, too coarse)
- K=74: Silhouette 0.021 (current viz)
- K=100: Silhouette 0.018 (recommended - balanced)
- K=150: Silhouette 0.016 (NIH Maps, lower quality)

Decision: Use K=100 for PROJECT_TERMS clustering
