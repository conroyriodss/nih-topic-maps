import requests
import os
import json
from google.cloud import storage
from datetime import datetime

def fetch_nih_data(request):
    """
    Fetches Smart and Connected Health (SCH) project data from NIH RePORTER API
    and stores the raw JSON response in a Google Cloud Storage bucket.
    """
    
    # Configuration
    NIH_REPORTER_API_URL = "https://api.reporter.nih.gov/v2/projects/search"
    GCS_BUCKET_NAME = os.environ.get("GCS_BUCKET_NAME")
    
    if not GCS_BUCKET_NAME:
        print("Error: GCS_BUCKET_NAME environment variable not set.")
        return "Error: GCS_BUCKET_NAME environment variable not set.", 500

    storage_client = storage.Client()
    bucket = storage_client.bucket(GCS_BUCKET_NAME)

    search_criteria = {
        "criteria": {
            "advanced_text_search": {
                "search_field": "all",
                "search_term": "\"Smart and Connected Health\"",
                "operator": "and"
            }
        },
        "offset": 0,
        "limit": 500  # Max limit per request
    }

    all_projects = []
    page = 0
    total_records = None

    print(f"Starting NIH RePORTER data fetch for '{search_criteria['criteria']['advanced_text_search']['search_term']}'...")

    while True:
        search_criteria["offset"] = page * search_criteria["limit"]
        print(f"Fetching page {page + 1} (offset: {search_criteria['offset']})...")

        try:
            response = requests.post(NIH_REPORTER_API_URL, json=search_criteria, timeout=30)
            response.raise_for_status()  # Raise an exception for HTTP errors
            data = response.json()

            if total_records is None:
                total_records = data.get("total", 0)
                print(f"Found {total_records} total records.")
            
            projects = data.get("results", [])
            all_projects.extend(projects)

            if len(all_projects) >= total_records:
                break # All records fetched
            
            page += 1

        except requests.exceptions.Timeout:
            print(f"Warning: Request timed out for page {page + 1}. Retrying or skipping...")
            # Implement retry logic if necessary, for now, just continue
            page += 1 # Move to next page to avoid infinite loop on timeout
        except requests.exceptions.RequestException as e:
            print(f"Error fetching data from NIH RePORTER API: {e}")
            return f"Error fetching data: {e}", 500
        except json.JSONDecodeError as e:
            print(f"Error decoding JSON response: {e}")
            print(f"Response content: {response.text}")
            return f"Error decoding JSON: {e}", 500

    if not all_projects:
        print("No projects found for the given criteria.")
        return "No projects found.", 200

    # Save to GCS
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    blob_name = f"nih_raw_data/nih_sch_projects_{timestamp}.json"
    blob = bucket.blob(blob_name)
    
    try:
        blob.upload_from_string(json.dumps(all_projects, indent=2), content_type="application/json")
        print(f"Successfully uploaded {len(all_projects)} projects to gs://{GCS_BUCKET_NAME}/{blob_name}")
        return f"Successfully fetched and stored {len(all_projects)} NIH SCH projects.", 200
    except Exception as e:
        print(f"Error uploading data to GCS: {e}")
        return f"Error uploading data to GCS: {e}", 500

