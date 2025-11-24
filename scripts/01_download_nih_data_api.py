#!/usr/bin/env python3
"""
Download NIH ExPORTER data using RePORTER API
Project: od-cl-odss-conroyri-f75a
Simplified version - downloads all projects directly
"""

import requests
import pandas as pd
import json
import time
from datetime import datetime
import subprocess
import sys

# Configuration
PROJECT_ID = "od-cl-odss-conroyri-f75a"
BUCKET = "gs://od-cl-odss-conroyri-nih-raw-data"
API_BASE_URL = "https://api.reporter.nih.gov/v2/projects/search"

# Fiscal years to download
FISCAL_YEARS = list(range(2020, 2026))  # 2020-2025

# API limits
MAX_OFFSET = 14999
BATCH_SIZE = 500

def download_projects_for_year(fiscal_year):
    """
    Download all projects for a fiscal year
    Downloads in batches up to the 15K offset limit
    """
    
    print(f"\n{'='*60}")
    print(f"Downloading Projects for FY{fiscal_year}")
    print(f"{'='*60}")
    
    all_projects = []
    offset = 0
    
    while offset < MAX_OFFSET:
        print(f"  Fetching records {offset:,} to {offset + BATCH_SIZE:,}...", end="", flush=True)
        
        payload = {
            "criteria": {
                "fiscal_years": [fiscal_year]
            },
            "offset": offset,
            "limit": BATCH_SIZE,
            "include_fields": [
                "ApplId",
                "SubprojectId", 
                "FiscalYear",
                "Organization",
                "AwardAmount",
                "AwardNoticeDate",
                "Agency",
                "AgencyIcFundings",
                "ContactPiName",
                "FullProjectNum",
                "OrgCity",
                "OrgCountry",
                "OrgDept",
                "OrgDistrict",
                "OrgDuns",
                "OrgFips",
                "OrgName",
                "OrgState",
                "OrgZipcode",
                "PhrText",
                "PiIds",
                "PiNames",
                "ProgramOfficerName",
                "ProjectStartDate",
                "ProjectEndDate",
                "ProjectTerms",
                "ProjectTitle",
                "ProjectNum",
                "ProjectSerialNum",
                "StudySection",
                "StudySectionName",
                "SuffixCode"
            ],
            "sort_field": "ApplId",
            "sort_order": "asc"
        }
        
        try:
            response = requests.post(API_BASE_URL, json=payload, timeout=60)
            response.raise_for_status()
            
            data = response.json()
            results = data.get("results", [])
            
            if not results:
                print(" No more records")
                break
            
            all_projects.extend(results)
            total_count = data.get("meta", {}).get("total", 0)
            print(f" ✓ ({len(results)} records, {total_count:,} total available)")
            
            # Check if we've reached the end or hit the offset limit
            if offset + BATCH_SIZE >= total_count:
                print(f"  ✓ All records retrieved for FY{fiscal_year}")
                break
            
            if offset + BATCH_SIZE >= MAX_OFFSET:
                print(f"  ⚠ Hit API offset limit of {MAX_OFFSET}")
                print(f"  Retrieved {len(all_projects):,} of {total_count:,} total projects")
                print(f"  Missing ~{total_count - len(all_projects):,} projects")
                break
            
            offset += BATCH_SIZE
            time.sleep(0.3)  # Rate limiting
            
        except requests.exceptions.RequestException as e:
            print(f"\n    Error: {e}")
            time.sleep(2)
            break
        except Exception as e:
            print(f"\n    Unexpected error: {e}")
            break
    
    if all_projects:
        # Convert to DataFrame
        df = pd.json_normalize(all_projects)
        df = df.drop_duplicates(subset=['appl_id'])
        
        print(f"\n  Total unique projects downloaded: {len(df):,}")
        
        # Save locally
        local_path = f"data/raw/projects_fy{fiscal_year}.csv"
        df.to_csv(local_path, index=False, encoding='utf-8')
        print(f"  ✓ Saved to {local_path}")
        
        # Upload to GCS
        gcs_path = f"{BUCKET}/projects/fy{fiscal_year}/projects_fy{fiscal_year}.csv"
        result = subprocess.run([
            'gsutil', 'cp', local_path, gcs_path
        ], capture_output=True, text=True)
        
        if result.returncode == 0:
            print(f"  ✓ Uploaded to {gcs_path}")
        else:
            print(f"  ⚠ Upload warning: {result.stderr}")
        
        return len(df)
    
    return 0

def download_abstracts_for_year(fiscal_year):
    """
    Download abstracts for a fiscal year
    Uses project IDs from already-downloaded projects file
    """
    
    print(f"\n{'='*60}")
    print(f"Downloading Abstracts for FY{fiscal_year}")
    print(f"{'='*60}")
    
    # Load project IDs from the projects file
    try:
        projects_df = pd.read_csv(f"data/raw/projects_fy{fiscal_year}.csv")
    except FileNotFoundError:
        print(f"  ⚠ Projects file not found for FY{fiscal_year}, skipping abstracts")
        return 0
    
    project_ids = projects_df['appl_id'].unique().tolist()
    print(f"  Found {len(project_ids):,} projects to get abstracts for")
    
    all_abstracts = []
    
    # Get abstracts in batches
    batch_size = 100
    total_batches = (len(project_ids) + batch_size - 1) // batch_size
    
    for i in range(0, len(project_ids), batch_size):
        batch = project_ids[i:i+batch_size]
        batch_num = i // batch_size + 1
        
        if batch_num % 20 == 0:  # Print every 20 batches
            print(f"  Batch {batch_num}/{total_batches}...", end="", flush=True)
        
        payload = {
            "criteria": {
                "appl_ids": batch
            },
            "offset": 0,
            "limit": batch_size,
            "include_fields": [
                "ApplId",
                "AbstractText",
                "PhrText",
                "ProjectTitle"
            ]
        }
        
        try:
            response = requests.post(API_BASE_URL, json=payload, timeout=60)
            response.raise_for_status()
            
            results = response.json().get("results", [])
            all_abstracts.extend(results)
            
            if batch_num % 20 == 0:
                print(f" ✓ ({len(all_abstracts):,} total)")
            
            time.sleep(0.3)  # Rate limiting
            
        except Exception as e:
            if batch_num % 20 == 0:
                print(f"\n  Error: {e}")
            continue
    
    if all_abstracts:
        # Convert to DataFrame
        df = pd.json_normalize(all_abstracts)
        df = df.drop_duplicates(subset=['appl_id'])
        
        print(f"\n  Total unique abstracts: {len(df):,}")
        
        # Save locally
        local_path = f"data/raw/abstracts_fy{fiscal_year}.csv"
        df.to_csv(local_path, index=False, encoding='utf-8')
        print(f"  ✓ Saved to {local_path}")
        
        # Upload to GCS
        gcs_path = f"{BUCKET}/abstracts/fy{fiscal_year}/abstracts_fy{fiscal_year}.csv"
        result = subprocess.run([
            'gsutil', 'cp', local_path, gcs_path
        ], capture_output=True, text=True)
        
        if result.returncode == 0:
            print(f"  ✓ Uploaded to {gcs_path}")
        else:
            print(f"  ⚠ Upload warning: {result.stderr}")
        
        return len(df)
    
    return 0

def main():
    """Main execution"""
    
    print(f"\n{'#'*60}")
    print(f"# NIH Data Download Pipeline (API Method)")
    print(f"# Project: {PROJECT_ID}")
    print(f"# Simplified version - direct download")
    print(f"# Start time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'#'*60}\n")
    
    start_time = time.time()
    total_projects = 0
    total_abstracts = 0
    
    year_stats = []
    
    for year in FISCAL_YEARS:
        year_start = time.time()
        
        try:
            # Download projects
            project_count = download_projects_for_year(year)
            total_projects += project_count
            
            # Download abstracts
            abstract_count = download_abstracts_for_year(year)
            total_abstracts += abstract_count
            
            year_elapsed = time.time() - year_start
            year_stats.append({
                'year': year,
                'projects': project_count,
                'abstracts': abstract_count,
                'time_min': year_elapsed / 60
            })
            
        except Exception as e:
            print(f"\n❌ Error processing FY{year}: {e}")
            import traceback
            traceback.print_exc()
            continue
    
    total_elapsed = time.time() - start_time
    
    print(f"\n{'='*60}")
    print(f"DOWNLOAD COMPLETE")
    print(f"{'='*60}")
    print(f"Total time: {total_elapsed/60:.1f} minutes")
    print(f"Total projects: {total_projects:,}")
    print(f"Total abstracts: {total_abstracts:,}")
    
    print(f"\n{'='*60}")
    print(f"Summary by Year:")
    print(f"{'='*60}")
    for stat in year_stats:
        print(f"  FY{stat['year']}: {stat['projects']:,} projects, "
              f"{stat['abstracts']:,} abstracts ({stat['time_min']:.1f} min)")
    
    # List local files
    print(f"\n{'='*60}")
    print(f"Downloaded files:")
    print(f"{'='*60}")
    result = subprocess.run(['ls', '-lh', 'data/raw/'], 
                          capture_output=True, text=True)
    print(result.stdout)
    
    print(f"\n{'='*60}")
    print(f"Cloud Storage:")
    print(f"{'='*60}")
    result = subprocess.run(['gsutil', 'ls', f'{BUCKET}/projects/'], 
                          capture_output=True, text=True)
    print(result.stdout)
    
    print(f"\nEnd time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"\nNext step: Load data to BigQuery")
    print(f"  python3 scripts/02_load_to_bigquery.py")

if __name__ == "__main__":
    main()
