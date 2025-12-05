#!/bin/bash

echo "======================================================================"
echo "FIX AND SYNC TO GITHUB"
echo "======================================================================"

echo ""
echo "[1/3] Pulling remote changes..."
git pull --rebase origin main

if [ $? -eq 0 ]; then
    echo "   ✅ Pull successful"
else
    echo "   ⚠️  Pull had conflicts - please resolve manually"
    exit 1
fi

echo ""
echo "[2/3] Checking status..."
git status --short | head -20

echo ""
echo "[3/3] Pushing to GitHub..."
git push origin main

if [ $? -eq 0 ]; then
    echo ""
    echo "======================================================================"
    echo "✅ SUCCESSFULLY SYNCED TO GITHUB"
    echo "======================================================================"
    echo ""
    echo "Session Summary:"
    echo "  ✅ Hierarchical clustering: 15 → 60 → 180 clusters"
    echo "  ✅ Interactive maps created"
    echo "  ✅ Documentation complete"
    echo "  ✅ GitHub synced"
    echo ""
    echo "Key Deliverables:"
    echo "  📊 award_map_hierarchical.html"
    echo "  📁 awards_hierarchical_clustered.csv"
    echo "  📖 README_DEC3_SESSION.md"
    echo ""
    echo "Session completed: $(date '+%Y-%m-%d %H:%M:%S %Z')"
    echo "======================================================================"
else
    echo ""
    echo "⚠️  Push failed. Check git status and try again."
fi
