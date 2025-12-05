#!/bin/bash
echo "Monitoring clustering completion..."
echo "Started at: $(date)"
echo ""

while true; do
    # Check if output file exists in GCS
    if gsutil ls gs://od-cl-odss-conroyri-nih-embeddings/hierarchical_50k_clustered.csv &>/dev/null; then
        echo ""
        echo "✅ CLUSTERING COMPLETE! ($(date))"
        echo ""
        echo "Downloading results..."
        gsutil cp gs://od-cl-odss-conroyri-nih-embeddings/hierarchical_50k_clustered.csv .
        
        echo ""
        echo "File info:"
        ls -lh hierarchical_50k_clustered.csv
        wc -l hierarchical_50k_clustered.csv
        
        echo ""
        echo "⚠️  REMEMBER TO DELETE VM:"
        echo "  gcloud compute instances delete nih-clustering-vm --zone=us-central1-a --quiet"
        echo ""
        break
    fi
    
    echo "⏳ Still processing... (checking every 30 seconds)"
    sleep 30
done
