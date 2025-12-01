# Context for Next Session

## Current State
- Working visualization at http://localhost:8000
- 43,320 grants clustered (FY 2000-2024)
- 5 domains x 13 topics x 24 subtopics

## Next Task
Expand dataset with 1990-1999 historical data from BigQuery to create denser spider web layout.

## Commands to Start
cd ~/nih-topic-maps
python3 -m http.server 8000 &
bq query --use_legacy_sql=false --format=json --max_rows=600000 'SELECT APPLICATION_ID, PROJECT_TITLE, PROJECT_TERMS, FY, IC_NAME, TOTAL_COST FROM od-cl-odss-conroyri-f75a.nih_exporter.projects WHERE FY BETWEEN 1990 AND 1999 AND PROJECT_TITLE IS NOT NULL' > grants_1990_1999_full.json

## Future Work
- Phase 2: Topic network view (creates spider web connections between topics)
