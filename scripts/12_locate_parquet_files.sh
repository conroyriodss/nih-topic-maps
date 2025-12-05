#!/bin/bash

echo "Searching for parquet files..."
echo ""

gsutil ls -r gs://od-cl-odss-conroyri-nih-embeddings/ | grep -i "\.parquet$" | head -30

echo ""
echo "Done. Copy the paths above and I'll load them to BigQuery."
