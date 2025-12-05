#!/bin/bash
# NIH Topic Maps - Complete Home Directory Cleanup Script
# Purpose: Audit entire home directory, organize NIH project, archive to GCS, clean unnecessary files
# Generated: 2025-12-05

set -euo pipefail

# ============================================
# CONFIGURATION - UPDATE THESE VALUES
# ============================================
PROJECT_ID="od-cl-odss-conroyri-f75a"
GCS_BUCKET="gs://od-cl-odss-conroyri-nih-processed/workspace-archive"
BQ_DATASET="nih_topic_maps"
HOME_DIR="$HOME"
NIH_PROJECT_DIR="$HOME/nih-topic-maps"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

NIH_EMBEDDINGS_BUCKET="gs://od-cl-odss-conroyri-nih-embeddings"
NIH_PROCESSED_BUCKET="gs://od-cl-odss-conroyri-nih-processed"
NIH_RAW_BUCKET="gs://od-cl-odss-conroyri-nih-raw-data"
NIH_WEBAPP_BUCKET="gs://od-cl-odss-conroyri-nih-webapp"

# Color output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

log_info() { echo -e "${BLUE}[INFO]${NC} $1"; }
log_success() { echo -e "${GREEN}[SUCCESS]${NC} $1"; }
log_warning() { echo -e "${YELLOW}[WARNING]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }

# ============================================
# STEP 1: COMPLETE HOME DIRECTORY AUDIT
# ============================================
audit_home_directory() {
    log_info "Auditing complete home directory..."
    
    AUDIT_FILE="$HOME/home_directory_audit_${TIMESTAMP}.txt"
    
    {
        echo "=========================================="
        echo "HOME DIRECTORY COMPLETE AUDIT"
        echo "Date: $(date)"
        echo "User: $(whoami)"
        echo "Home: $HOME"
        echo "=========================================="
        echo ""
        
        echo "=== DISK USAGE BY TOP-LEVEL DIRECTORY ==="
        du -h -d 1 "$HOME" 2>/dev/null | sort -hr | head -20
        echo ""
        
        echo "=== ALL TOP-LEVEL ITEMS ==="
        ls -lah "$HOME" 2>/dev/null
        echo ""
        
        echo "=== HIDDEN FILES AND DIRECTORIES ==="
        find "$HOME" -maxdepth 1 -name ".*" -type f -o -name ".*" -type d | head -50
        echo ""
        
        echo "=== LARGE FILES (>50MB) ==="
        find "$HOME" -type f -size +50M 2>/dev/null | xargs ls -lh 2>/dev/null | head -30
        echo ""
        
        echo "=== PYTHON ENVIRONMENTS ==="
        find "$HOME" -maxdepth 3 -type d -name "venv" -o -name ".venv" -o -name "env" 2>/dev/null
        echo ""
        
        echo "=== GIT REPOSITORIES ==="
        find "$HOME" -maxdepth 3 -type d -name ".git" 2>/dev/null | sed 's/\/.git$//'
        echo ""
        
        echo "=== JUPYTER/IPYTHON ==="
        du -sh "$HOME/.jupyter" 2>/dev/null || echo "No .jupyter directory"
        du -sh "$HOME/.ipython" 2>/dev/null || echo "No .ipython directory"
        echo ""
        
        echo "=== GOOGLE CLOUD SDK ==="
        du -sh "$HOME/.config/gcloud" 2>/dev/null || echo "No gcloud config"
        echo ""
        
        echo "=== CACHE DIRECTORIES ==="
        du -sh "$HOME/.cache" 2>/dev/null || echo "No .cache"
        du -sh "$HOME/.local" 2>/dev/null || echo "No .local"
        echo ""
        
        echo "=== TEMPORARY FILES ==="
        find "$HOME" -maxdepth 2 -name "*.tmp" -o -name "*.log" -o -name "*~" 2>/dev/null | wc -l
        echo ""
        
        echo "=== RECOMMENDATION: FOLDERS TO KEEP ==="
        echo "✓ nih-topic-maps (PROJECT - organize and archive)"
        echo "✓ .config (system configuration)"
        echo "✓ .ssh (SSH keys)"
        echo "✓ .bashrc, .bash_profile (shell config)"
        echo ""
        
        echo "=== RECOMMENDATION: SAFE TO REMOVE ==="
        echo "✗ Old git clones (archive first if needed)"
        echo "✗ Test/demo projects"
        echo "✗ Python virtual environments (can recreate)"
        echo "✗ .cache/* (safe to delete)"
        echo "✗ Jupyter checkpoints"
        echo "✗ Temporary files (*.tmp, *.log, *~)"
        
    } > "$AUDIT_FILE"
    
    log_success "Complete audit saved to: $AUDIT_FILE"
    cat "$AUDIT_FILE"
}

# ============================================
# STEP 2: CREATE NIH PROJECT STRUCTURE
# ============================================
create_nih_project_structure() {
    log_info "Creating standardized NIH project structure..."
    
    mkdir -p "$NIH_PROJECT_DIR"/{scripts,notebooks,data/{raw,processed},outputs/{reports,exports},archive/{phase1,phase2},config,docs,logs}
    
    log_success "NIH project directory structure created"
}

# ============================================
# STEP 3: ARCHIVE NIH PROJECT TO GCS
# ============================================
archive_nih_project_to_gcs() {
    log_info "Archiving NIH project files to GCS..."
    
    if [ ! -d "$NIH_PROJECT_DIR" ]; then
        log_warning "NIH project directory not found, skipping archive"
        return
    fi
    
    cd "$NIH_PROJECT_DIR"
    
    # Archive all important file types
    for ext in py ipynb sql sh md json yaml yml parquet csv; do
        FILES=$(find . -name "*.$ext" -type f 2>/dev/null)
        if [ -n "$FILES" ]; then
            log_info "Archiving .$ext files..."
            echo "$FILES" | while read file; do
                gsutil cp "$file" "${GCS_BUCKET}/workspace_archive/${TIMESTAMP}/$file" 2>/dev/null || true
            done
        fi
    done
    
    log_success "NIH project archived to GCS"
}

# ============================================
# STEP 4: ORGANIZE NIH PROJECT FILES
# ============================================
organize_nih_project() {
    log_info "Organizing NIH project files..."
    
    if [ ! -d "$NIH_PROJECT_DIR" ]; then
        log_warning "NIH project directory not found"
        return
    fi
    
    cd "$NIH_PROJECT_DIR"
    
    # Move files to appropriate directories
    find . -maxdepth 1 -name "*.py" -type f -exec mv {} scripts/ 2>/dev/null \; || true
    find . -maxdepth 1 -name "*.ipynb" -type f -exec mv {} notebooks/ 2>/dev/null \; || true
    find . -maxdepth 1 -name "*.sql" -type f -exec mv {} scripts/ 2>/dev/null \; || true
    find . -maxdepth 1 -name "*.sh" -type f ! -name "cleanup.sh" -exec mv {} scripts/ 2>/dev/null \; || true
    find . -maxdepth 1 -name "*.csv" -type f -exec mv {} data/processed/ 2>/dev/null \; || true
    find . -maxdepth 1 -name "*.parquet" -type f -exec mv {} data/processed/ 2>/dev/null \; || true
    find . -maxdepth 1 -name "*.json" -type f -exec mv {} data/processed/ 2>/dev/null \; || true
    
    log_success "NIH project files organized"
}

# ============================================
# STEP 5: CLEAN CACHE AND TEMPORARY FILES
# ============================================
clean_cache_and_temp() {
    log_info "Cleaning cache and temporary files..."
    
    # Python cache
    find "$HOME" -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
    find "$HOME" -type d -name ".ipynb_checkpoints" -exec rm -rf {} + 2>/dev/null || true
    find "$HOME" -name "*.pyc" -delete 2>/dev/null || true
    
    # Temporary files
    find "$HOME" -maxdepth 2 -name "*.tmp" -delete 2>/dev/null || true
    find "$HOME" -maxdepth 2 -name "*~" -delete 2>/dev/null || true
    
    # User cache (be careful)
    if [ -d "$HOME/.cache" ]; then
        log_warning "Cleaning .cache directory (pip, etc.)..."
        rm -rf "$HOME/.cache/pip" 2>/dev/null || true
        rm -rf "$HOME/.cache/matplotlib" 2>/dev/null || true
    fi
    
    log_success "Cache and temporary files cleaned"
}

# ============================================
# STEP 6: AUDIT BIGQUERY TABLES
# ============================================
audit_gcs_buckets() {
    log_info "Auditing GCS buckets..."
    
    GCS_AUDIT="$HOME/gcs_buckets_audit_${TIMESTAMP}.txt"
    
    {
        echo "=========================================="
        echo "GCS BUCKETS AUDIT"
        echo "Date: $(date)"
        echo "=========================================="
        echo ""
        
        echo "=== ALL BUCKETS ==="
        gsutil ls
        echo ""
        
        echo "=== NIH PROJECT BUCKETS - DETAILED ==="
        
        for bucket in $NIH_EMBEDDINGS_BUCKET $NIH_PROCESSED_BUCKET $NIH_RAW_BUCKET $NIH_WEBAPP_BUCKET; do
            echo ""
            echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
            echo "BUCKET: $bucket"
            echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
            
            echo "Total size:"
            gsutil du -sh "$bucket" 2>/dev/null || echo "  Cannot calculate size"
            echo ""
            
            echo "Top-level structure:"
            gsutil ls "$bucket" 2>/dev/null | head -20 || echo "  Empty or inaccessible"
            echo ""
            
            echo "File counts:"
            echo "  Parquet: $(gsutil ls -r "$bucket/**/*.parquet" 2>/dev/null | grep -v ':$' | wc -l)"
            echo "  CSV: $(gsutil ls -r "$bucket/**/*.csv" 2>/dev/null | grep -v ':$' | wc -l)"
            echo "  JSON: $(gsutil ls -r "$bucket/**/*.json" 2>/dev/null | grep -v ':$' | wc -l)"
            echo "  Python: $(gsutil ls -r "$bucket/**/*.py" 2>/dev/null | grep -v ':$' | wc -l)"
            echo "  Notebooks: $(gsutil ls -r "$bucket/**/*.ipynb" 2>/dev/null | grep -v ':$' | wc -l)"
            echo ""
            
            echo "Largest files (top 10):"
            gsutil ls -lh "$bucket/**" 2>/dev/null | grep -v ':$' | sort -k1 -hr | head -10 || echo "  None found"
            echo ""
        done
        
        echo ""
        echo "=== NON-NIH BUCKETS (Review for cleanup) ==="
        echo "gs://gcf-v2-sources-* - Google Cloud Functions (system-managed)"
        echo "gs://gcf-v2-uploads-* - Google Cloud Functions (system-managed)"
        echo "gs://nih-analytics-embeddings/ - Old embeddings? Consolidate?"
        echo "gs://nih-analytics-exports/ - Old exports? Consolidate?"
        echo "gs://run-sources-* - Cloud Run (system-managed)"
        echo ""
        
        echo "=== BUCKET ORGANIZATION RECOMMENDATIONS ==="
        echo ""
        echo "KEEP and ORGANIZE:"
        echo "✓ od-cl-odss-conroyri-nih-embeddings/ - Phase 2 embeddings"
        echo "  └── Organize: /phase1/, /phase2/, /production/"
        echo ""
        echo "✓ od-cl-odss-conroyri-nih-processed/ - Processed data"
        echo "  └── Organize: /grant-cards/, /clusters/, /exports/, /workspace-archive/"
        echo ""
        echo "✓ od-cl-odss-conroyri-nih-raw-data/ - Raw source data"
        echo "  └── Organize: /nih-reporter/, /historical/, /supplements/"
        echo ""
        echo "✓ od-cl-odss-conroyri-nih-webapp/ - Web application assets"
        echo "  └── Keep as-is if currently deployed"
        echo ""
        echo "REVIEW for consolidation/deletion:"
        echo "? gs://nih-analytics-embeddings/ - Merge into od-cl-odss-conroyri-nih-embeddings?"
        echo "? gs://nih-analytics-exports/ - Merge into od-cl-odss-conroyri-nih-processed?"
        echo ""
        echo "LEAVE ALONE (system-managed):"
        echo "• gs://gcf-v2-sources-*"
        echo "• gs://gcf-v2-uploads-*"
        echo "• gs://run-sources-*"
        echo ""
        
        echo "=== SUGGESTED CLEANUP COMMANDS ==="
        echo ""
        echo "# Create organized structure in processed bucket:"
        echo "gsutil -m cp -r ${NIH_PROCESSED_BUCKET}/* ${NIH_PROCESSED_BUCKET}/archive-${TIMESTAMP}/"
        echo ""
        echo "# If old buckets are obsolete, copy then delete:"
        echo "# gsutil -m cp -r gs://nih-analytics-embeddings/* ${NIH_EMBEDDINGS_BUCKET}/legacy/"
        echo "# gsutil -m rm -r gs://nih-analytics-embeddings"
        echo ""
        echo "# gsutil -m cp -r gs://nih-analytics-exports/* ${NIH_PROCESSED_BUCKET}/legacy-exports/"
        echo "# gsutil -m rm -r gs://nih-analytics-exports"
        
    } > "$GCS_AUDIT"
    
    log_success "GCS buckets audit saved to: $GCS_AUDIT"
    cat "$GCS_AUDIT"
}

organize_gcs_buckets() {
    log_info "Organizing GCS bucket structure..."
    
    log_info "Creating organized folders in processed bucket..."
    
    echo "Workspace archives" | gsutil cp - "${NIH_PROCESSED_BUCKET}/workspace-archive/.folder_marker" 2>/dev/null || true
    echo "Grant cards" | gsutil cp - "${NIH_PROCESSED_BUCKET}/grant-cards/.folder_marker" 2>/dev/null || true
    echo "Cluster data" | gsutil cp - "${NIH_PROCESSED_BUCKET}/clusters/.folder_marker" 2>/dev/null || true
    echo "Data exports" | gsutil cp - "${NIH_PROCESSED_BUCKET}/exports/.folder_marker" 2>/dev/null || true
    echo "Analysis reports" | gsutil cp - "${NIH_PROCESSED_BUCKET}/reports/.folder_marker" 2>/dev/null || true
    
    echo "Phase 1 embeddings" | gsutil cp - "${NIH_EMBEDDINGS_BUCKET}/phase1/.folder_marker" 2>/dev/null || true
    echo "Phase 2 embeddings" | gsutil cp - "${NIH_EMBEDDINGS_BUCKET}/phase2/.folder_marker" 2>/dev/null || true
    echo "Production embeddings" | gsutil cp - "${NIH_EMBEDDINGS_BUCKET}/production/.folder_marker" 2>/dev/null || true
    
    echo "NIH Reporter data" | gsutil cp - "${NIH_RAW_BUCKET}/nih-reporter/.folder_marker" 2>/dev/null || true
    echo "Historical data" | gsutil cp - "${NIH_RAW_BUCKET}/historical/.folder_marker" 2>/dev/null || true
    
    log_success "GCS bucket organization complete"
    log_info "Manual step: Move existing files into organized structure as needed"
}

audit_bigquery_tables() {
    log_info "Auditing BigQuery tables..."
    
    BQ_AUDIT="$HOME/bigquery_audit_${TIMESTAMP}.txt"
    
    {
        echo "=========================================="
        echo "BIGQUERY TABLES AUDIT"
        echo "Dataset: $BQ_DATASET"
        echo "Date: $(date)"
        echo "=========================================="
        echo ""
        
        echo "=== ALL TABLES ==="
        bq ls --project_id="$PROJECT_ID" --max_results=100 "$BQ_DATASET" || echo "Error listing tables"
        echo ""
        
        echo "=== TABLE DETAILS ==="
        for table in $(bq ls --project_id="$PROJECT_ID" "$BQ_DATASET" 2>/dev/null | tail -n +3 | awk '{print $1}'); do
            echo "--- $table ---"
            bq show --project_id="$PROJECT_ID" "${BQ_DATASET}.${table}" 2>/dev/null || echo "Error showing table"
            echo ""
        done
        
        echo "=== CLEANUP RECOMMENDATIONS ==="
        echo "1. Tables to KEEP:"
        echo "   - award_clustering (253,487 awards - Phase 2)"
        echo "   - grant_cards_* (all entity cards)"
        echo "   - embeddings/UMAP results"
        echo ""
        echo "2. Tables to REVIEW for deletion:"
        echo "   - temp_* (temporary tables)"
        echo "   - test_* (test tables)"
        echo "   - staging_* (staging tables)"
        echo "   - *_backup_* (old backups)"
        echo ""
        echo "3. To delete a table, run:"
        echo "   bq rm -f ${BQ_DATASET}.table_name"
        
    } > "$BQ_AUDIT"
    
    log_success "BigQuery audit saved to: $BQ_AUDIT"
    cat "$BQ_AUDIT"
}

# ============================================
# STEP 7: GENERATE DOCUMENTATION
# ============================================
generate_documentation() {
    log_info "Generating workspace documentation..."
    
    mkdir -p "$NIH_PROJECT_DIR/docs"
    
    cat > "$NIH_PROJECT_DIR/docs/WORKSPACE_STRUCTURE.md" << 'EOFMARKER'
# NIH Topic Maps - Workspace Structure

**Last Updated:** $(date)

## Directory Organization

~/nih-topic-maps/
├── scripts/           # Python, SQL, shell scripts
├── notebooks/         # Jupyter notebooks
├── data/
│   ├── raw/          # Original data (rare - mostly in BigQuery)
│   └── processed/    # Exported/processed files
├── outputs/
│   ├── reports/      # Generated analysis reports
│   └── exports/      # Data exports (CSV, JSON)
├── archive/
│   ├── phase1/       # Phase 1 clustering work
│   └── phase2/       # Phase 2 clustering work (COMPLETED)
├── config/           # Configuration files
├── docs/             # Documentation
└── logs/             # Execution logs

## Data Sources

### Primary Data Location
- **BigQuery Dataset:** `nih_topic_maps`
- **GCS Buckets:**
  - `od-cl-odss-conroyri-nih-embeddings/` - Embeddings and UMAP coordinates
  - `od-cl-odss-conroyri-nih-processed/` - Processed data, grant cards, exports
  - `od-cl-odss-conroyri-nih-raw-data/` - Raw NIH Reporter data
  - `od-cl-odss-conroyri-nih-webapp/` - Web application assets

### Key BigQuery Tables
- `award_clustering` - 253,487 awards with Phase 2 cluster assignments
- `grant_cards_award` - Award-level grant cards
- `grant_cards_pi` - PI aggregations
- `grant_cards_ic` - IC aggregations  
- `grant_cards_institution` - Institution aggregations

## Phase 2 Status (COMPLETED)

✅ **Completed:**
- 253,487 awards clustered
- Grant cards updated with clustering metadata
- VM deleted
- Workspace cleaned and organized

⏳ **Next Steps:**
1. Rebuild entity cards with complete Phase 2 data
2. Generate cluster/topic summaries
3. Create domain analysis reports
4. Build PI collaboration networks

## File Naming Conventions

- `build_*.py` - Pipeline construction
- `analyze_*.py` - Analysis scripts
- `export_*.py` - Data export utilities
- `explore_*.ipynb` - EDA notebooks
- `report_*.ipynb` - Report generation
- `*_YYYYMMDD.*` - Dated snapshots

## Maintenance

- **Weekly:** Review logs for errors
- **Monthly:** Run cleanup script, audit BigQuery tables
- **Quarterly:** Archive old notebooks/scripts to GCS
- **Annual:** Review and update documentation
EOFMARKER

    log_success "Documentation created: $NIH_PROJECT_DIR/docs/WORKSPACE_STRUCTURE.md"
}

# ============================================
# STEP 8: DRY RUN - SHOW WHAT WOULD BE DELETED
# ============================================
dry_run_deletions() {
    log_warning "===== DRY RUN: Files/Folders that COULD be deleted ====="
    log_warning "Review these carefully before uncommenting deletion commands"
    echo ""
    
    echo "=== LARGE FILES (>100MB) - Consider archiving first ==="
    find "$HOME" -type f -size +100M 2>/dev/null | head -20
    echo ""
    
    echo "=== OLD GIT REPOSITORIES (not nih-topic-maps) ==="
    find "$HOME" -maxdepth 2 -type d -name ".git" 2>/dev/null | grep -v "nih-topic-maps" | sed 's/\/.git$//'
    echo ""
    
    echo "=== PYTHON VIRTUAL ENVIRONMENTS ==="
    find "$HOME" -maxdepth 3 -type d \( -name "venv" -o -name ".venv" -o -name "env" \) 2>/dev/null
    echo ""
    
    echo "=== TEST/DEMO DIRECTORIES ==="
    find "$HOME" -maxdepth 2 -type d \( -name "*test*" -o -name "*demo*" -o -name "*tmp*" \) 2>/dev/null | head -20
    echo ""
}

# ============================================
# MAIN EXECUTION
# ============================================
main() {
    log_info "Starting NIH Topic Maps complete workspace cleanup..."
    log_info "Timestamp: $TIMESTAMP"
    echo ""
    
    # Validate configuration
    if [[ "$PROJECT_ID" == "YOUR_PROJECT_ID" ]] || [[ "$GCS_BUCKET" == "gs://YOUR_BUCKET"* ]]; then
        log_error "ERROR: Update PROJECT_ID and GCS_BUCKET at top of script"
        exit 1
    fi
    
    # Execute all steps
    audit_home_directory
    echo ""; echo ""
    
    audit_gcs_buckets
    echo ""; echo ""
    
    create_nih_project_structure
    archive_nih_project_to_gcs
    organize_nih_project
    organize_gcs_buckets
    clean_cache_and_temp
    audit_bigquery_tables
    generate_documentation
    
    echo ""; echo ""
    dry_run_deletions
    
    echo ""; echo ""
    log_success "===== CLEANUP COMPLETE ====="
    log_info "Next steps:"
    log_info "1. Review audit files:"
    log_info "   - home_directory_audit_${TIMESTAMP}.txt"
    log_info "   - gcs_buckets_audit_${TIMESTAMP}.txt"
    log_info "   - bigquery_audit_${TIMESTAMP}.txt"
    log_info "2. Review GCS bucket organization in: ${NIH_PROCESSED_BUCKET}/"
    log_info "3. Verify workspace archive: ${GCS_BUCKET}/${TIMESTAMP}/"
    log_info "4. Review dry run output above"
    log_info "5. Consider consolidating old buckets (nih-analytics-*)"
    log_info "6. Manually delete unnecessary folders after confirmation"
    log_info "7. Read documentation: ~/nih-topic-maps/docs/WORKSPACE_STRUCTURE.md"
    echo ""
    log_info "Ready to proceed with entity card rebuild!"
}

# Execute
main
