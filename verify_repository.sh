#!/bin/bash
# Verify repository structure and file integrity

echo "========================================================================"
echo "Repository Verification"
echo "========================================================================"
echo ""

cd ~/nih-topic-maps

# Check directory structure
echo "Checking directory structure..."
REQUIRED_DIRS="scripts data/processed docs archive validationreports"
for dir in $REQUIRED_DIRS; do
    if [ -d "$dir" ]; then
        echo "  OK $dir"
    else
        echo "  MISSING $dir - creating..."
        mkdir -p "$dir"
    fi
done

echo ""
echo "========================================================================"
echo "Core Documentation Files"
echo "========================================================================"
if [ -f "CONTEXT_FOR_NEXT_SESSION.md" ]; then
    echo "  OK CONTEXT_FOR_NEXT_SESSION.md"
    echo "     Last modified: $(stat -c %y CONTEXT_FOR_NEXT_SESSION.md 2>/dev/null | cut -d' ' -f1)"
else
    echo "  MISSING CONTEXT_FOR_NEXT_SESSION.md"
fi

if [ -f "README_GPU_PIPELINE.md" ]; then
    echo "  OK README_GPU_PIPELINE.md"
else
    echo "  MISSING README_GPU_PIPELINE.md"
fi

if [ -f "PROJECTLOG.md" ]; then
    echo "  OK PROJECTLOG.md"
else
    echo "  MISSING PROJECTLOG.md"
fi

echo ""
echo "========================================================================"
echo "GPU Pipeline Scripts"
echo "========================================================================"
PIPELINE_SCRIPTS="launch_gpu_vm.sh deploy_and_run_embeddings.sh monitor_gpu_vm.sh check_results_and_cleanup.sh emergency_stop_vm.sh run_gpu_pipeline.sh fix_and_restart_vm.sh"
for script in $PIPELINE_SCRIPTS; do
    if [ -f "$script" ] && [ -x "$script" ]; then
        echo "  OK $script (executable)"
    elif [ -f "$script" ]; then
        echo "  WARNING $script (not executable)"
        chmod +x "$script"
        echo "     Fixed: made executable"
    else
        echo "  MISSING $script"
    fi
done

echo ""
echo "========================================================================"
echo "Python Analysis Scripts"
echo "========================================================================"
PYTHON_SCRIPTS="scripts/05b_generate_embeddings_project_terms.py scripts/06_cluster_project_terms.py scripts/check_k_results.py scripts/compare_clustering_methods.py scripts/analyze_clustering.py scripts/find_optimal_k.py"
for script in $PYTHON_SCRIPTS; do
    if [ -f "$script" ]; then
        echo "  OK $script"
    else
        echo "  MISSING $script"
    fi
done

echo ""
echo "========================================================================"
echo "Visualization Files"
echo "========================================================================"
VIZ_FILES="createfullvizv6.html index.html icmapping.json"
for file in $VIZ_FILES; do
    if [ -f "$file" ]; then
        SIZE=$(du -h "$file" | cut -f1)
        echo "  OK $file ($SIZE)"
    else
        echo "  MISSING $file"
    fi
done

echo ""
echo "========================================================================"
echo "GCS Bucket Contents"
echo "========================================================================"
echo "Checking embeddings in GCS..."
gsutil ls gs://od-cl-odss-conroyri-nih-embeddings/sample/ 2>/dev/null | grep -E "embeddings|manifest|cluster|viz" | while read line; do
    SIZE=$(gsutil du -h "$line" 2>/dev/null | awk '{print $1}')
    FILENAME=$(basename "$line")
    echo "  OK $FILENAME ($SIZE)"
done

echo ""
echo "========================================================================"
echo "Git Repository Status"
echo "========================================================================"
echo "Branch: $(git branch --show-current 2>/dev/null || echo 'unknown')"
echo "Last commit: $(git log -1 --oneline 2>/dev/null || echo 'no commits')"
echo ""
echo "Uncommitted changes:"
git status --short 2>/dev/null || echo "  None or git not initialized"

echo ""
echo "========================================================================"
echo "System Requirements Check"
echo "========================================================================"
echo "Cloud SDK:"
which gcloud >/dev/null && echo "  OK gcloud installed" || echo "  MISSING gcloud"

echo "Python:"
which python3 >/dev/null && echo "  OK python3 installed ($(python3 --version 2>&1))" || echo "  MISSING python3"

echo "Git:"
which git >/dev/null && echo "  OK git installed ($(git --version 2>&1))" || echo "  MISSING git"

echo ""
echo "========================================================================"
echo "Verification Complete"
echo "========================================================================"
echo ""
echo "If any files are MISSING, regenerate them from the session notes."
echo "All GPU pipeline scripts should be executable."
