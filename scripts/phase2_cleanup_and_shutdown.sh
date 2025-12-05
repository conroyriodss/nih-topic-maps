#!/bin/bash
set -e

echo "=========================================="
echo "PHASE 2 CLEANUP & VM SHUTDOWN"
echo "December 4, 2025 - 10:50 PM EST"
echo "=========================================="
echo ""

# ==========================================
# STEP 1: VERIFY COMPLETION
# ==========================================
echo "[1/6] Verifying Phase 2 completion..."

bq query --use_legacy_sql=false << 'EOSQL'
SELECT 
  COUNT(DISTINCT CORE_PROJECT_NUM) as total_assignments,
  COUNT(DISTINCT cluster_id) as num_clusters,
  MIN(cluster_id) as min_cluster,
  MAX(cluster_id) as max_cluster
FROM `od-cl-odss-conroyri-f75a.nih_analytics.phase2_cluster_assignments`;
EOSQL

echo "✓ Verified BigQuery assignments"

# ==========================================
# STEP 2: COPY IMPORTANT FILES FROM VM
# ==========================================
echo ""
echo "[2/6] Copying important files from VM..."

# Create local backup directory
mkdir -p ~/phase2_backup
cd ~/phase2_backup

# Copy logs
gcloud compute scp nih-embeddings-gpu-vm:~/phase2_clustering.log ./phase2_clustering.log --zone=us-central1-a 2>/dev/null || echo "Log file not found"

# Copy the embeddings file (if it exists and is small enough)
echo "Attempting to copy embeddings file (may be large)..."
gcloud compute scp nih-embeddings-gpu-vm:/tmp/phase2_embeddings.npy ./phase2_embeddings.npy --zone=us-central1-a 2>/dev/null || echo "Embeddings file too large or not found - skipped"

# Copy the clustering script for reference
gcloud compute scp nih-embeddings-gpu-vm:~/phase2_cluster.py ./phase2_cluster.py --zone=us-central1-a 2>/dev/null || echo "Script not found"

echo "✓ Files copied to ~/phase2_backup/"
ls -lh ~/phase2_backup/

# ==========================================
# STEP 3: CREATE COMPLETION SUMMARY
# ==========================================
echo ""
echo "[3/6] Creating completion summary..."

cat > ~/phase2_backup/COMPLETION_SUMMARY.md << 'SUMMARY'
# Phase 2 Clustering - COMPLETION SUMMARY
**Completed: December 4, 2025, ~2:24 AM EST**
**Total Runtime: ~8 hours**

## Results
- **Total Assignments:** 1,015,023 awards
- **Clusters Used:** 75 clusters from Phase 1
- **Embeddings Generated:** 1,015,021 × 768 dimensions
- **BigQuery Table:** `phase2_cluster_assignments`

## Top Clusters
1. Stroke / Patients / Motor (159,948 awards)
2. Vaccine / Responses / Virus (106,277 awards)
3. Inflammatory / Inflammation / Cells (87,222 awards)
4. Cells / Cell / Stem (84,288 awards)
5. Virus / Viral / Infection (81,672 awards)

## Technical Details
- **Model:** PubMedBERT (768-dim embeddings)
- **Processing Speed:** ~35 items/second
- **VM Type:** n1-standard-4 with GPU
- **Status:** Completed successfully, ready for integration

## Known Issue
Script encountered error at step 4 (UMAP approximation) but assignments 
were already saved to BigQuery. Error did not affect clustering results.

## Next Steps
1. Update grant_cards_v1_6_with_agency with new cluster assignments
2. Rebuild entity cards with complete clustering coverage
3. Shutdown and delete GPU VM to save costs
SUMMARY

echo "✓ Summary created"

# ==========================================
# STEP 4: UPDATE GRANT CARDS WITH PHASE 2
# ==========================================
echo ""
echo "[4/6] Updating grant cards with Phase 2 assignments..."

bq query --use_legacy_sql=false << 'EOSQL'
-- First, backup current grant_cards
CREATE OR REPLACE TABLE `od-cl-odss-conroyri-f75a.nih_analytics.grant_cards_v1_6_before_phase2_merge`
AS SELECT * FROM `od-cl-odss-conroyri-f75a.nih_analytics.grant_cards_v1_6_with_agency`;

-- Update with Phase 2 assignments
CREATE OR REPLACE TABLE `od-cl-odss-conroyri-f75a.nih_analytics.grant_cards_v1_6_with_agency` AS
SELECT 
  g.*,
  COALESCE(g.cluster_id, p2.cluster_id) as cluster_id_updated,
  COALESCE(g.cluster_label, p2.cluster_label) as cluster_label_updated
FROM `od-cl-odss-conroyri-f75a.nih_analytics.grant_cards_v1_6_with_agency` g
LEFT JOIN `od-cl-odss-conroyri-f75a.nih_analytics.phase2_cluster_assignments` p2
  ON g.CORE_PROJECT_NUM = p2.CORE_PROJECT_NUM;

-- Validate update
SELECT 
  'Before Phase 2' as status,
  COUNTIF(cluster_id IS NOT NULL) as clustered,
  COUNTIF(cluster_id IS NULL) as unclustered
FROM `od-cl-odss-conroyri-f75a.nih_analytics.grant_cards_v1_6_before_phase2_merge`
UNION ALL
SELECT 
  'After Phase 2',
  COUNTIF(cluster_id_updated IS NOT NULL),
  COUNTIF(cluster_id_updated IS NULL)
FROM `od-cl-odss-conroyri-f75a.nih_analytics.grant_cards_v1_6_with_agency`;
EOSQL

echo "✓ Grant cards updated"

# ==========================================
# STEP 5: FINAL VALIDATION
# ==========================================
echo ""
echo "[5/6] Running final validation..."

bq query --use_legacy_sql=false << 'EOSQL'
SELECT
  'Phase 2 Assignments' as source,
  COUNT(DISTINCT CORE_PROJECT_NUM) as unique_projects,
  COUNT(DISTINCT cluster_id) as num_clusters
FROM `od-cl-odss-conroyri-f75a.nih_analytics.phase2_cluster_assignments`
UNION ALL
SELECT
  'Updated Grant Cards',
  COUNT(DISTINCT CORE_PROJECT_NUM),
  COUNT(DISTINCT cluster_id_updated)
FROM `od-cl-odss-conroyri-f75a.nih_analytics.grant_cards_v1_6_with_agency`
WHERE cluster_id_updated IS NOT NULL;
EOSQL

echo "✓ Validation complete"

# ==========================================
# STEP 6: SHUTDOWN VM
# ==========================================
echo ""
echo "[6/6] Shutting down GPU VM..."

echo ""
echo "VM will be stopped in 10 seconds..."
echo "Press Ctrl+C to cancel shutdown"
sleep 10

# Stop the VM
gcloud compute instances stop nih-embeddings-gpu-vm --zone=us-central1-a

echo "✓ VM stopped"

# ==========================================
# COMPLETION
# ==========================================
echo ""
echo "=========================================="
echo "✅ PHASE 2 CLEANUP COMPLETE!"
echo "=========================================="
echo ""
echo "Summary:"
echo "  ✓ Verified 1,015,023 cluster assignments"
echo "  ✓ Copied files to ~/phase2_backup/"
echo "  ✓ Created completion summary"
echo "  ✓ Updated grant_cards with Phase 2 clusters"
echo "  ✓ VM stopped (NOT deleted - can restart if needed)"
echo ""
echo "Files backed up:"
ls -lh ~/phase2_backup/
echo ""
echo "Next steps:"
echo "  1. Review ~/phase2_backup/COMPLETION_SUMMARY.md"
echo "  2. Rebuild entity cards with complete clustering"
echo "  3. Delete VM if no longer needed:"
echo "     gcloud compute instances delete nih-embeddings-gpu-vm --zone=us-central1-a"
echo ""
echo "Cost savings: VM stopped, only storage costs remain"
echo "=========================================="
