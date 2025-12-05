#!/bin/bash

VM_NAME="clustering-phase2-vm"
ZONE="us-central1-a"
PROJECT_ID="od-cl-odss-conroyri-f75a"

echo "Checking Phase 2 clustering status..."
echo ""

# Check if process is running
gcloud compute ssh $VM_NAME --zone=$ZONE --command='
if [ -f clustering.pid ]; then
  PID=$(cat clustering.pid)
  if ps -p $PID > /dev/null; then
    echo "✓ Clustering is RUNNING (PID: $PID)"
    echo ""
    echo "Last 20 lines of log:"
    tail -n 20 phase2_clustering.log
  else
    echo "✓ Clustering has COMPLETED"
    echo ""
    echo "Last 50 lines of log:"
    tail -n 50 phase2_clustering.log
  fi
else
  echo "⚠ No clustering process found"
fi
'

echo ""
echo "Checking BigQuery table..."
ROW_COUNT=$(bq query --use_legacy_sql=false --format=csv --max_rows=1 \
  "SELECT COUNT(*) as cnt FROM \`$PROJECT_ID.nih_analytics.phase2_cluster_assignments\` WHERE 1=1 LIMIT 1" 2>/dev/null | tail -n 1)

if [ ! -z "$ROW_COUNT" ]; then
  echo "✓ phase2_cluster_assignments table exists"
  echo "  Rows: $ROW_COUNT"
else
  echo "⚠ phase2_cluster_assignments table not yet created"
fi

echo ""
