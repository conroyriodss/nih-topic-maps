#!/usr/bin/env python3
"""
Create IC abbreviation to full name mapping
"""

IC_MAPPING = {
    'AA': 'NIAAA',    # National Institute on Alcohol Abuse and Alcoholism
    'AG': 'NIA',      # National Institute on Aging
    'AI': 'NIAID',    # National Institute of Allergy and Infectious Diseases
    'AR': 'NIAMS',    # National Institute of Arthritis and Musculoskeletal and Skin Diseases
    'AT': 'NCCIH',    # National Center for Complementary and Integrative Health
    'CA': 'NCI',      # National Cancer Institute
    'DA': 'NIDA',     # National Institute on Drug Abuse
    'DC': 'NIDCD',    # National Institute on Deafness and Other Communication Disorders
    'DE': 'NIDCR',    # National Institute of Dental and Craniofacial Research
    'DK': 'NIDDK',    # National Institute of Diabetes and Digestive and Kidney Diseases
    'EB': 'NIBIB',    # National Institute of Biomedical Imaging and Bioengineering
    'ES': 'NIEHS',    # National Institute of Environmental Health Sciences
    'EY': 'NEI',      # National Eye Institute
    'GM': 'NIGMS',    # National Institute of General Medical Sciences
    'HD': 'NICHD',    # Eunice Kennedy Shriver National Institute of Child Health and Human Development
    'HL': 'NHLBI',    # National Heart, Lung, and Blood Institute
    'LM': 'NLM',      # National Library of Medicine
    'MD': 'NIMHD',    # National Institute on Minority Health and Health Disparities
    'MH': 'NIMH',     # National Institute of Mental Health
    'NS': 'NINDS',    # National Institute of Neurological Disorders and Stroke
    'NR': 'NINR',     # National Institute of Nursing Research
    'TR': 'NCATS',    # National Center for Advancing Translational Sciences
    'TW': 'FIC',      # Fogarty International Center
    'RR': 'NCRR',     # National Center for Research Resources (merged into NCATS)
    'OD': 'OD',       # Office of the Director
    'CIT': 'CIT',     # Center for Information Technology
    'FIC': 'FIC'      # Fogarty International Center
}

import json
with open('ic_mapping.json', 'w') as f:
    json.dump(IC_MAPPING, f, indent=2)

print("✓ IC mapping created")
