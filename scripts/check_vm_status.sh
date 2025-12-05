#!/bin/bash
echo "=============================================="
echo "VM CLUSTERING STATUS CHECK"
echo "=============================================="
echo ""
echo "VM Status:"
gcloud compute instances describe nih-clustering-vm --zone=us-central1-a \
  --format="table(name,status,machineType)" 2>/dev/null || echo "VM not found"

echo ""
echo "Checking for output in GCS..."
gsutil ls -lh gs://od-cl-odss-conroyri-nih-embeddings/hierarchical_50k_clustered.csv 2>/dev/null \
  && echo "✅ Clustering complete! File found in GCS." \
  || echo "⏳ Still processing... (check again in a few minutes)"

echo ""
echo "VM has been running for:"
CREATED=$(gcloud compute instances describe nih-clustering-vm --zone=us-central1-a \
  --format="get(creationTimestamp)" 2>/dev/null)
if [ ! -z "$CREATED" ]; then
  START_SEC=$(date -d "$CREATED" +%s 2>/dev/null || date -j -f "%Y-%m-%dT%H:%M:%S" "$CREATED" +%s 2>/dev/null)
  NOW_SEC=$(date +%s)
  ELAPSED=$((NOW_SEC - START_SEC))
  MINUTES=$((ELAPSED / 60))
  echo "  $MINUTES minutes"
  echo "  Estimated cost so far: \$$(echo "scale=2; $MINUTES * 0.50 / 60" | bc)"
fi

echo ""
echo "To check VM logs:"
echo "  gcloud compute ssh nih-clustering-vm --zone=us-central1-a --command='tail -20 ~/workspace/*.log'"
echo ""
echo "To delete VM when done:"
echo "  gcloud compute instances delete nih-clustering-vm --zone=us-central1-a --quiet"
echo "=============================================="
