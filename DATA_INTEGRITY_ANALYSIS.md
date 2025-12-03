# Data Integrity Analysis: ExPORTER Dataset

## Current Understanding of Data Schema

From your 250K analysis, we have:
- APPLICATION_ID (primary key)
- PROJECT_TITLE (used for clustering/labeling)
- IC_NAME (75 unique institutes/centers)
- FY (fiscal year: 2000-2024)
- TOTAL_COST (funding amount)
- cluster_k75 (our computed cluster assignment)

**Missing/Not Yet Utilized:**
- PI information (names, institutions)
- Institution details (names, locations)
- Core project numbers (grouping related grants)
- RCDC categories (NIH research categories)
- Project terms/abstracts (if available)

---

## Data Integrity Checks Needed

### 1. Grant-Level Integrity

Let's check what we have:
