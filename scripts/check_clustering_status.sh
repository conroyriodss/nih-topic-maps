#!/bin/bash
set -e

VM_NAME="nih-embeddings-gpu-vm"
ZONE="us-central1-a"
PROJECT_ID="od-cl-odss-conroyri-f75a"

echo "=========================================="
echo "PHASE 2 CLUSTERING STATUS CHECK"
echo "=========================================="
echo ""

# Check if VM exists and is running
echo "[1/3] Checking VM status..."
VM_STATUS=$(gcloud compute instances describe $VM_NAME --zone=$ZONE --format="get(status)" 2>/dev/null || echo "NOT_FOUND")

if [ "$VM_STATUS" = "NOT_FOUND" ]; then
  echo "⚠ VM not found: $VM_NAME"
  echo ""
  echo "VM may have been deleted or never created."
  exit 1
elif [ "$VM_STATUS" != "RUNNING" ]; then
  echo "⚠ VM exists but is $VM_STATUS"
  echo ""
  echo "Start it with:"
  echo "  gcloud compute instances start $VM_NAME --zone=$ZONE"
  exit 1
else
  echo "✓ VM is RUNNING"
fi

# Check if clustering process is running
echo ""
echo "[2/3] Checking clustering process..."
PROCESS_STATUS=$(gcloud compute ssh $VM_NAME --zone=$ZONE --command='
if [ -f clustering.pid ]; then
  PID=$(cat clustering.pid)
  if ps -p $PID > /dev/null 2>&1; then
    echo "RUNNING:$PID"
  else
    echo "COMPLETED:$PID"
  fi
else
  echo "NOT_STARTED"
fi
' 2>/dev/null)

if [[ $PROCESS_STATUS == RUNNING:* ]]; then
  PID="${PROCESS_STATUS#RUNNING:}"
  echo "✓ Clustering is RUNNING (PID: $PID)"
  echo ""
  echo "Latest output:"
  echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
  gcloud compute ssh $VM_NAME --zone=$ZONE --command='tail -n 30 phase2_clustering.log' 2>/dev/null
  echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
elif [[ $PROCESS_STATUS == COMPLETED:* ]]; then
  echo "✓ Clustering has COMPLETED"
  echo ""
  echo "Final output:"
  echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
  gcloud compute ssh $VM_NAME --zone=$ZONE --command='tail -n 50 phase2_clustering.log' 2>/dev/null
  echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
else
  echo "⚠ Clustering process not started"
  echo ""
  echo "Log file status:"
  gcloud compute ssh $VM_NAME --zone=$ZONE --command='
if [ -f phase2_clustering.log ]; then
  echo "Log exists, last 20 lines:"
  tail -n 20 phase2_clustering.log
else
  echo "No log file found"
fi
' 2>/dev/null
fi

# Check BigQuery table
echo ""
echo "[3/3] Checking BigQuery results..."
RESULT_COUNT=$(bq query --use_legacy_sql=false --format=csv --max_rows=1 \
  "SELECT COUNT(*) as cnt FROM \`$PROJECT_ID.nih_analytics.phase2_cluster_assignments\`" 2>/dev/null | tail -n 1)

if [ ! -z "$RESULT_COUNT" ] && [ "$RESULT_COUNT" != "cnt" ]; then
  echo "✓ BigQuery table exists with $RESULT_COUNT assignments"
  
  # Get sample
  echo ""
  echo "Sample results:"
  bq query --use_legacy_sql=false << 'EOSQL'
SELECT 
  cluster_id,
  cluster_label,
  COUNT(*) as num_awards
FROM `od-cl-odss-conroyri-f75a.nih_analytics.phase2_cluster_assignments`
GROUP BY cluster_id, cluster_label
ORDER BY num_awards DESC
LIMIT 5;
EOSQL
else
  echo "⚠ No results in BigQuery yet"
fi

echo ""
echo "=========================================="
echo "STATUS SUMMARY"
echo "=========================================="
echo "VM: $VM_STATUS"
echo "Process: ${PROCESS_STATUS%%:*}"
if [ ! -z "$RESULT_COUNT" ] && [ "$RESULT_COUNT" != "cnt" ]; then
  echo "Results: $RESULT_COUNT assignments in BigQuery"
else
  echo "Results: Not available yet"
fi
echo ""

# Recommendations
if [[ $PROCESS_STATUS == RUNNING:* ]]; then
  echo "⏳ Clustering in progress. Check again in 30-60 minutes."
  echo ""
  echo "Watch live:"
  echo "  gcloud compute ssh $VM_NAME --zone=$ZONE --command='tail -f phase2_clustering.log'"
elif [[ $PROCESS_STATUS == COMPLETED:* ]] && [ ! -z "$RESULT_COUNT" ] && [ "$RESULT_COUNT" != "cnt" ]; then
  echo "✅ CLUSTERING COMPLETE! Ready to update grant cards."
  echo ""
  echo "Next step:"
  echo "  ./update_grant_cards_after_completion.sh"
else
  echo "ℹ️  Clustering may have failed or not started."
  echo ""
  echo "Restart clustering:"
  echo "  gcloud compute ssh $VM_NAME --zone=$ZONE"
  echo "  nohup python3 phase2_cluster.py > phase2_clustering.log 2>&1 &"
fi

echo "=========================================="
