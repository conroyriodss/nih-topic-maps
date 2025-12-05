#!/bin/bash
echo "======================================================================"
echo "CHECKING BIGQUERY SCHEMA FOR ADDITIONAL FIELDS"
echo "======================================================================"

bq show --schema --format=prettyjson nih-oer-prod-odss:exporter_analytics.prod_projects | \
python3 -c "
import sys
import json

schema = json.load(sys.stdin)

print('\nAvailable fields in ExPORTER dataset:\n')

categories = {
    'Grant Identifiers': ['APPLICATION_ID', 'CORE_PROJECT_NUM', 'PROJECT_NUMBER'],
    'Project Info': ['PROJECT_TITLE', 'PROJECT_START_DATE', 'PROJECT_END_DATE', 'FY', 'AWARD_NOTICE_DATE'],
    'PI/Personnel': ['PI_NAMEs', 'CONTACT_PI_NAME', 'PROGRAM_OFFICER_NAME'],
    'Institution': ['ORG_NAME', 'ORG_CITY', 'ORG_STATE', 'ORG_COUNTRY', 'ORG_DEPT', 'ORG_DUNS'],
    'IC/Agency': ['IC_NAME', 'ADMINISTERING_IC', 'FUNDING_ICs', 'NIH_SPENDING_CATS'],
    'Funding': ['TOTAL_COST', 'DIRECT_COST_AMT', 'INDIRECT_COST_AMT'],
    'Classification': ['ACTIVITY_CODE', 'STUDY_SECTION', 'PROJECT_TERMS', 'PHR', 'SERIAL_NUMBER'],
    'Research Categories': ['RCDC_categories']
}

found_fields = {cat: [] for cat in categories}
other_fields = []

for field in schema:
    name = field['name']
    ftype = field['type']
    matched = False
    
    for category, keywords in categories.items():
        if any(kw.lower() in name.lower() for kw in keywords):
            found_fields[category].append(f\"  • {name:40s} ({ftype})\")
            matched = True
            break
    
    if not matched:
        other_fields.append(f\"  • {name:40s} ({ftype})\")

for category, fields in found_fields.items():
    if fields:
        print(f'\n{category}:')
        for field in sorted(fields):
            print(field)

if other_fields:
    print(f'\nOther Fields:')
    for field in sorted(other_fields)[:20]:
        print(field)
    if len(other_fields) > 20:
        print(f'  ... and {len(other_fields) - 20} more')
"
