#!/bin/bash
set -e

echo "=========================================="
echo "REBUILDING ALL ENTITY CARDS"
echo "Using grant_scorecard_v2 (COMPREHENSIVE)"
echo "=========================================="
echo ""

echo "[1/3] Building PI cards..."
./rebuild_comprehensive_pi_cards.sh

echo ""
echo "[2/3] Building Institution cards..."
./rebuild_comprehensive_institution_cards.sh

echo ""
echo "[3/3] Building Temporal trends..."
./rebuild_comprehensive_temporal_trends.sh

echo ""
echo "=========================================="
echo "✅ ALL COMPREHENSIVE CARDS COMPLETE!"
echo "=========================================="
echo ""
echo "Tables created:"
echo "  - ic_cards_comprehensive"
echo "  - pi_cards_comprehensive"
echo "  - institution_cards_comprehensive"
echo "  - temporal_trends_comprehensive"
echo ""
