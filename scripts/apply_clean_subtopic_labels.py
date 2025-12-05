#!/usr/bin/env python3
import json

print("Loading hierarchy...")
with open('viz_data_3level_hierarchy.json') as f:
    hier_data = json.load(f)

# Clean, distinctive labels for each subtopic
label_map = {
    0: "Training Programs",
    2: "Clinical Research",
    3: "Global Health Programs",
    4: "Diagnostic Imaging",
    6: "Neuroscience",
    7: "Viral Mechanisms",
    8: "Behavioral & Obesity",
    9: "Xenograft Models",
    13: "Animal Models & Aging",
    14: "Gene Expression",
    15: "Protein Engineering",
    16: "Vaccine Development",
    17: "Immunization",
    18: "Genetic Testing",
    19: "Research Infrastructure",
    20: "Adolescent Interventions",
    21: "Applied Research",
    22: "Research Development",
    23: "Risk Assessment",
    24: "Cellular Regulation",
    25: "Clinical Translation",
    26: "Women's Health",
    27: "Cell Biology",
    28: "Cellular Function"
}

# Apply labels
for subtopic in hier_data['subtopics']:
    st_id = subtopic['id']
    if st_id in label_map:
        subtopic['label'] = label_map[st_id]

# Save
with open('viz_data_3level_hierarchy.json', 'w') as f:
    json.dump(hier_data, f)

print("✅ Clean subtopic labels applied")

