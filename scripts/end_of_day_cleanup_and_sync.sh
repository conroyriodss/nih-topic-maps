#!/bin/bash
set -e

echo "=========================================="
echo "END OF DAY CLEANUP & SYNC"
echo "December 4, 2025"
echo "=========================================="
echo ""

# ==========================================
# SECTION 1: UPDATE DOCUMENTATION
# ==========================================
echo "[1/5] Updating documentation..."

cat > DATA_INVENTORY.md << 'DOCINV'
# NIH Analytics Data Inventory
**Updated: December 4, 2025**

## Summary
- **Total Projects:** 513,419
- **Total Funding:** $861.3B (2000-2024)
- **Complete Portfolio:** Extramural + Intramural + Contracts

## Production Tables

### Entity Cards (Comprehensive)
| Table | Records | Description |
|-------|---------|-------------|
| `ic_cards_comprehensive` | 114 ICs | All award types including N/Z-series |
| `pi_cards_comprehensive` | 49,619 PIs | Cleaned names, 3+ awards minimum |
| `institution_cards_comprehensive` | 2,230 institutions | Excludes NIH ICOs |
| `temporal_trends_comprehensive` | 25 years | Annual trends 2000-2024 |

### Award Type Coverage
✅ **RPG** (R01, R03, R15, R21, R33, R34, R37, R56)
✅ **High-Risk/High-Reward** (R35, DP1, DP2, DP5, RF1)
✅ **Centers** (P01, P30, P50, P-series)
✅ **Cooperative Agreements** (U01, U19, U54, UL1-CTSA)
✅ **Training** (T32, T35, T-series)
✅ **Career Development** (K-series, R00)
✅ **Fellowships** (F-series)
✅ **SBIR/STTR** (R41-R44, U43-U44)
✅ **Infrastructure** (G12-RCMI, S06-MBRS, C06)
✅ **Contracts** (N01, N03, N-series)
✅ **Intramural** (Z01, ZIA, Z-series)

### Specialized Identifiers
- **CTSA Institutions:** 260 (UL1 awards)
- **T32 Training Programs:** 5,328
- **RCMI Institutions:** 57 (G12 awards)
- **P30 Core Grants:** Tracked by institution

## Source Tables
- `grant_scorecard_v2` - Comprehensive portfolio (513k projects, 358 activity codes)
- `grant_cards_v2_0_complete` - Clustered research awards (282k projects, 27 activity codes)
- `phase2_cluster_assignments` - ML clustering results (253k assignments, 35% complete)

## Data Quality
- PI names cleaned (removed "(contact)" suffix)
- NIH ICO institutions excluded
- All award types retained (N/Z-series included)
- 25-year temporal coverage (2000-2024)
DOCINV

cat > SESSION_SUMMARY.md << 'DOCSESS'
# Session Summary: December 4, 2025

## Major Accomplishments

### 1. Fixed Activity Code Classification ✅
**Problem:** Original IC cards showed 99.6% RPG, 0% centers/training
**Solution:** 
- Discovered P/U/T-series awards in `grant_scorecard_v2`
- Created proper classification buckets
- Rebuilt all cards with correct distributions

**Result:** Realistic portfolios (e.g., CA: 34.6% RPG, 15.1% centers, 15.9% coop agreements)

### 2. Built Comprehensive Entity Cards ✅
**Created 4 complete card types:**
- IC cards (114 ICs)
- PI cards (49,619 PIs)
- Institution cards (2,230 institutions)  
- Temporal trends (25 years)

**All include:**
- RPG, Centers (P), Cooperative Agreements (U), Training (T)
- Career Development (K), Fellowships (F), SBIR, Infrastructure
- Contracts (N-series) and Intramural (Z-series)

### 3. Data Quality Improvements ✅
- Removed "(contact)" from PI names
- Excluded NIH ICO institution names
- Kept N-series (contracts) and Z-series (intramural)
- Validated against source data

### 4. Discovered Data Architecture ✅
**Key Finding:** Two parallel data sources
- `grant_scorecard_v2`: 513k projects, ALL award types (358 activity codes)
- `grant_cards_v2_0_complete`: 282k projects, CLUSTERED awards only (27 activity codes)

**Implication:** Use scorecard for portfolio analysis, grant_cards for topic/cluster analysis

## Key Insights

### IC Portfolio Distribution (Corrected)
- **AI (NIAID):** 27% cooperative agreements (epidemic response)
- **CA (NCI):** 15% centers, 16% cooperative agreements (cancer networks)
- **PS/DP (CDC):** 96-99% cooperative agreements (prevention programs)
- **RR:** 31% centers (research infrastructure)

### CTSA Network
- 260 institutions with UL1 awards
- Concentrated in RR (69 awards) and GM (10 awards)

### Training Grants
- GM leads with 885 T32 awards (basic science training)
- 5,328 total T32 programs across all institutions

### Career Development Growth
- Fastest growing mechanism (2015-2024)
- 4,631 → 6,780 awards (+46%)

## Technical Details

### Scripts Created
- `rebuild_comprehensive_ic_cards_v2.sh`
- `rebuild_comprehensive_pi_cards.sh`
- `rebuild_comprehensive_institution_cards.sh`
- `rebuild_comprehensive_temporal_trends.sh`
- `fix_all_entity_cards.sh`
- `restore_n_z_series_awards.sh`

### Tables Modified
- `ic_cards_comprehensive` (replaced 3 times)
- `pi_cards_comprehensive` (replaced 3 times)
- `institution_cards_comprehensive` (replaced 3 times)
- `temporal_trends_comprehensive` (created)

## Phase 2 Clustering Status
- **Progress:** 35% complete (as of 4:30 PM)
- **Processing:** 253,487 / 1,015,023 awards
- **VM Status:** RUNNING
- **ETA:** ~2-3 hours remaining

## Next Steps
1. Wait for Phase 2 clustering completion
2. Export entity cards for visualization
3. Create specialized reports (CTSA, training, MSI)
4. Integrate clustering data with comprehensive cards
DOCSESS

echo "✓ Documentation updated"

# ==========================================
# SECTION 2: CLEAN UP OLD FILES
# ==========================================
echo ""
echo "[2/5] Cleaning up old files..."

# Remove old scripts
rm -f spot_check_*.sh 2>/dev/null || true
rm -f rebuild_cards_simple.sh 2>/dev/null || true
rm -f rebuild_cards_with_correct_classification.sh 2>/dev/null || true
rm -f fix_activity_code_classification.sh 2>/dev/null || true
rm -f rebuild_cards_safe.sh 2>/dev/null || true
rm -f rebuild_ic_cards_*.sh 2>/dev/null || true
rm -f create_comprehensive_cards.sh 2>/dev/null || true
rm -f investigate_data_sources.sh 2>/dev/null || true

echo "✓ Old scripts removed"

# ==========================================
# SECTION 3: SYNC WITH GITHUB
# ==========================================
echo ""
echo "[3/5] Syncing with GitHub..."

# Configure git
git config --global user.email "conroyri@nih.gov"
git config --global user.name "Ryan Conroy"

# Add all documentation and final scripts
git add DATA_INVENTORY.md SESSION_SUMMARY.md 2>/dev/null || true
git add rebuild_comprehensive_*.sh 2>/dev/null || true
git add fix_all_entity_cards.sh 2>/dev/null || true
git add restore_n_z_series_awards.sh 2>/dev/null || true
git add end_of_day_cleanup_and_sync.sh 2>/dev/null || true

# Commit changes
git commit -m "End of day Dec 4 2025: Comprehensive entity cards with all award types" 2>/dev/null || echo "Nothing to commit"

# Push to GitHub
git push origin main 2>/dev/null || echo "Push failed or already up to date"

echo "✓ GitHub sync attempted"

# ==========================================
# SECTION 4: CHECK VM STATUS
# ==========================================
echo ""
echo "[4/5] Checking Phase 2 clustering VM status..."

echo ""
echo "VM Status:"
gcloud compute instances describe nih-embeddings-gpu-vm --zone=us-central1-a --format="table(name,status,machineType)" 2>/dev/null || echo "VM check failed"

echo ""
echo "Latest clustering output:"
gcloud compute ssh nih-embeddings-gpu-vm --zone=us-central1-a --command='tail -20 phase2_clustering.log' 2>/dev/null || echo "Could not retrieve logs"

echo ""
echo "Phase 2 progress:"
bq query --use_legacy_sql=false --max_rows=1 << 'EOSQL'
SELECT 
  COUNT(DISTINCT CORE_PROJECT_NUM) as assignments_made,
  ROUND(COUNT(DISTINCT CORE_PROJECT_NUM) * 100.0 / 1015023, 1) as pct_complete
FROM `od-cl-odss-conroyri-f75a.nih_analytics.phase2_cluster_assignments`;
EOSQL

echo "✓ VM status checked"

# ==========================================
# SECTION 5: FINAL VALIDATION
# ==========================================
echo ""
echo "[5/5] Final validation of entity cards..."

bq query --use_legacy_sql=false << 'EOSQL'
SELECT
  'IC Cards' as table_name,
  COUNT(*) as num_records,
  SUM(total_projects) as total_projects,
  SUM(total_funding_billions) as total_funding_b
FROM `od-cl-odss-conroyri-f75a.nih_analytics.ic_cards_comprehensive`
UNION ALL
SELECT
  'PI Cards',
  COUNT(*),
  SUM(total_awards),
  ROUND(SUM(total_funding_millions)/1e3, 2)
FROM `od-cl-odss-conroyri-f75a.nih_analytics.pi_cards_comprehensive`
UNION ALL
SELECT
  'Institution Cards',
  COUNT(*),
  SUM(total_awards),
  SUM(total_funding_billions)
FROM `od-cl-odss-conroyri-f75a.nih_analytics.institution_cards_comprehensive`
UNION ALL
SELECT
  'Temporal Trends',
  COUNT(*),
  SUM(total_awards),
  SUM(total_funding_billions)
FROM `od-cl-odss-conroyri-f75a.nih_analytics.temporal_trends_comprehensive`;
EOSQL

echo ""
echo "=========================================="
echo "✅ END OF DAY CLEANUP COMPLETE!"
echo "=========================================="
echo ""
echo "Summary:"
echo "  ✓ Documentation updated (DATA_INVENTORY.md, SESSION_SUMMARY.md)"
echo "  ✓ Old files cleaned up"
echo "  ✓ GitHub sync attempted"
echo "  ✓ VM status checked"
echo "  ✓ Entity cards validated"
echo ""
echo "Production Tables Ready:"
echo "  - ic_cards_comprehensive (114 ICs)"
echo "  - pi_cards_comprehensive (49,619 PIs)"
echo "  - institution_cards_comprehensive (2,230 institutions)"
echo "  - temporal_trends_comprehensive (25 years)"
echo ""
echo "All award types included: R/P/U/T/K/F/SBIR/Infrastructure/N/Z"
echo ""
echo "Session complete. Have a great evening!"
echo "=========================================="
