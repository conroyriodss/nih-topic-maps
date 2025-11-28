# Term Filtering Strategy for PROJECT_TERMS

## Problem
PROJECT_TERMS contains two types of terms:
1. SCIENTIFIC: Diseases, conditions, methods, genes, proteins
2. GENERIC: Grant language (testing, goals, novel, research)

The generic terms pollute clustering because they appear in 16-47% of grants.

## Solution: Two-Dictionary Filtering

### Dictionary 1: KEEP LIST (Scientific Terms)
Source: MeSH + RCDC Thesaurus
Categories to keep:
- Diseases [C] - cancer, diabetes, alzheimer
- Chemicals and Drugs [D] - proteins, genes, compounds
- Anatomy [A] - brain, heart, liver
- Organisms [B] - bacteria, viruses, mice
- Analytical Techniques [E] - PCR, sequencing, imaging
- Phenomena and Processes [G] - apoptosis, inflammation

### Dictionary 2: REMOVE LIST (Grant Terminology)
Terms describing approach, not science:
- Grant structure: goals, aims, testing, development
- Generic research: novel, improved, innovative
- Populations: human, patients, individual
- Time/process: time, process, outcome, future
- Administrative: programs, research personnel

## Implementation Options

### Option A: MeSH Category Filtering
1. Download MeSH XML
2. Extract terms from categories A, B, C, D, E, G
3. Keep only PROJECT_TERMS that match MeSH
4. Result: Pure scientific vocabulary

### Option B: TF-IDF with MeSH Boost
1. Apply TF-IDF as before
2. Boost weight for terms found in MeSH
3. Reduce weight for non-MeSH terms
4. Result: Science-weighted embeddings

### Option C: Supervised Filtering
1. Sample 1000 PROJECT_TERMS manually
2. Label as SCIENCE vs GRANT-SPEAK
3. Train classifier
4. Filter all 45K unique terms
5. Result: Custom NIH filter

## Recommended Approach: Option A (MeSH Filtering)

Rationale:
- MeSH is authoritative (NLM maintained)
- Already hierarchical (can select categories)
- Free to download and use
- Aligns with MEDLINE/PubMed indexing

Steps:
1. Download MeSH descriptors
2. Extract terms from scientific categories
3. Create whitelist of ~25,000 terms
4. Filter PROJECT_TERMS against whitelist
5. Re-cluster with filtered terms

## Quick Implementation

For immediate testing, use MeSH category prefixes:
- Keep terms containing disease names (cancer, syndrome, disease)
- Keep terms with -itis, -osis, -emia (medical suffixes)
- Keep anatomical terms (brain, heart, cell, tissue)
- Keep method terms (PCR, assay, imaging, sequencing)
- Remove generic modifiers (novel, improved, new)
- Remove process words (testing, development, outcome)
