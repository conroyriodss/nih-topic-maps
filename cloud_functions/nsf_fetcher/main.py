import requests
import os
import json
from google.cloud import storage
from datetime import datetime

def fetch_nsf_data(request):
    """
    Fetches Smart and Connected Health (SCH) project data from the NSF Awards API
    and stores the raw JSON response in a Google Cloud Storage bucket.
    """
    
    # Configuration
    NSF_AWARDS_API_URL = "https://api.nsf.gov/services/v1/awards.json"
    GCS_BUCKET_NAME = os.environ.get("GCS_BUCKET_NAME")
    
    if not GCS_BUCKET_NAME:
        print("Error: GCS_BUCKET_NAME environment variable not set.")
        return "Error: GCS_BUCKET_NAME environment variable not set.", 500

    storage_client = storage.Client()
    bucket = storage_client.bucket(GCS_BUCKET_NAME)

    search_params = {
        "keyword": '"Smart and Connected Health"',
        "rpp": 25,  # Max results per page
        "offset": 1
    }

    all_awards = []
    page = 0

    print(f"Starting NSF Awards data fetch for keyword '{search_params['keyword']}'...")

    while True:
        search_params["offset"] = (page * search_params["rpp"]) + 1
        print(f"Fetching page {page + 1} (offset: {search_params['offset']})...")

        try:
            response = requests.get(NSF_AWARDS_API_URL, params=search_params, timeout=30)
            response.raise_for_status()
            data = response.json()
            
            awards = data.get("response", {}).get("award", [])
            if not awards:
                print("No more awards found. Ending fetch.")
                break
            
            all_awards.extend(awards)
            page += 1

        except requests.exceptions.Timeout:
            print(f"Warning: Request timed out for page {page + 1}. Retrying or skipping...")
            page += 1
        except requests.exceptions.RequestException as e:
            print(f"Error fetching data from NSF Awards API: {e}")
            return f"Error fetching data: {e}", 500
        except json.JSONDecodeError as e:
            print(f"Error decoding JSON response: {e}")
            print(f"Response content: {response.text}")
            return f"Error decoding JSON: {e}", 500

    if not all_awards:
        print("No awards found for the given criteria.")
        return "No awards found.", 200

    # Save to GCS
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    blob_name = f"nsf_raw_data/nsf_sch_awards_{timestamp}.json"
    blob = bucket.blob(blob_name)
    
    try:
        blob.upload_from_string(json.dumps(all_awards, indent=2), content_type="application/json")
        print(f"Successfully uploaded {len(all_awards)} awards to gs://{GCS_BUCKET_NAME}/{blob_name}")
        return f"Successfully fetched and stored {len(all_awards)} NSF SCH awards.", 200
    except Exception as e:
        print(f"Error uploading data to GCS: {e}")
        return f"Error uploading data to GCS: {e}", 500
