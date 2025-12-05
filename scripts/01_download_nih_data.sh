#!/bin/bash
# Download NIH ExPORTER data for fiscal years 2000-2025
# Project: od-cl-odss-conroyri-f75a

set -e  # Exit on error

BUCKET="gs://od-cl-odss-conroyri-nih-raw-data"
DATA_DIR="$HOME/nih-topic-maps/data/raw"

cd $DATA_DIR

echo "=== NIH Data Download Pipeline ==="
echo "Project: od-cl-odss-conroyri-f75a"
echo "Start time: $(date)"
echo ""

# Function to download and upload one fiscal year
download_year() {
    YEAR=$1
    echo "Processing FY${YEAR}..."
    
    # Download projects
    if [ ! -f "RePORTER_PRJ_C_FY${YEAR}.zip" ]; then
        echo "  Downloading projects..."
        wget -q --show-progress \
            https://exporter.nih.gov/CSVs/final/RePORTER_PRJ_C_FY${YEAR}.zip
    fi
    
    # Download abstracts
    if [ ! -f "RePORTER_PRJABS_C_FY${YEAR}.zip" ]; then
        echo "  Downloading abstracts..."
        wget -q --show-progress \
            https://exporter.nih.gov/CSVs/final/RePORTER_PRJABS_C_FY${YEAR}.zip
    fi
    
    # Unzip
    echo "  Unzipping..."
    unzip -q -o "RePORTER_PRJ_C_FY${YEAR}.zip"
    unzip -q -o "RePORTER_PRJABS_C_FY${YEAR}.zip"
    
    # Upload to GCS
    echo "  Uploading to Cloud Storage..."
    gsutil -m cp RePORTER_PRJ_C_FY${YEAR}.csv \
        ${BUCKET}/projects/fy${YEAR}/
    gsutil -m cp RePORTER_PRJABS_C_FY${YEAR}.csv \
        ${BUCKET}/abstracts/fy${YEAR}/
    
    # Clean up local files to save space
    rm -f *.zip
    rm -f RePORTER_*.csv
    
    echo "  ✓ FY${YEAR} complete"
    echo ""
}

# Download recent years first (2020-2025)
for year in {2020..2025}; do
    download_year $year
done

# Optionally download older years (2000-2019)
# Uncomment the next lines if you want full historical data
# for year in {2000..2019}; do
#     download_year $year
# done

echo "=== Download Complete ==="
echo "End time: $(date)"
echo ""
echo "To verify uploads:"
echo "  gsutil ls -lh ${BUCKET}/projects/"
echo "  gsutil ls -lh ${BUCKET}/abstracts/"
