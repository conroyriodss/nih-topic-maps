#!/bin/bash

PROJECT_ID="od-cl-odss-conroyri-f75a"
DATASET="nih_exporter"
BUCKET="gs://od-cl-odss-conroyri-nih-embeddings/exporter"

echo "======================================================================"
echo "Loading NIH ExPORTER Data to BigQuery (Year by Year)"
echo "======================================================================"

# Load PROJECTS - all years at once
echo ""
echo "Loading PROJECTS table (all years)..."
bq load --source_format=PARQUET \
  --replace \
  --autodetect \
  ${PROJECT_ID}:${DATASET}.projects \
  "${BUCKET}/projects_parquet/YEAR=1990/projects_1990.parquet" \
  "${BUCKET}/projects_parquet/YEAR=1991/projects_1991.parquet" \
  "${BUCKET}/projects_parquet/YEAR=1992/projects_1992.parquet" \
  "${BUCKET}/projects_parquet/YEAR=1993/projects_1993.parquet" \
  "${BUCKET}/projects_parquet/YEAR=1994/projects_1994.parquet" \
  "${BUCKET}/projects_parquet/YEAR=1995/projects_1995.parquet" \
  "${BUCKET}/projects_parquet/YEAR=1996/projects_1996.parquet" \
  "${BUCKET}/projects_parquet/YEAR=1997/projects_1997.parquet" \
  "${BUCKET}/projects_parquet/YEAR=1998/projects_1998.parquet" \
  "${BUCKET}/projects_parquet/YEAR=1999/projects_1999.parquet" \
  "${BUCKET}/projects_parquet/YEAR=2000/projects_2000.parquet" \
  "${BUCKET}/projects_parquet/YEAR=2001/projects_2001.parquet" \
  "${BUCKET}/projects_parquet/YEAR=2002/projects_2002.parquet" \
  "${BUCKET}/projects_parquet/YEAR=2003/projects_2003.parquet" \
  "${BUCKET}/projects_parquet/YEAR=2004/projects_2004.parquet" \
  "${BUCKET}/projects_parquet/YEAR=2005/projects_2005.parquet" \
  "${BUCKET}/projects_parquet/YEAR=2006/projects_2006.parquet" \
  "${BUCKET}/projects_parquet/YEAR=2007/projects_2007.parquet" \
  "${BUCKET}/projects_parquet/YEAR=2008/projects_2008.parquet" \
  "${BUCKET}/projects_parquet/YEAR=2009/projects_2009.parquet" \
  "${BUCKET}/projects_parquet/YEAR=2010/projects_2010.parquet" \
  "${BUCKET}/projects_parquet/YEAR=2011/projects_2011.parquet" \
  "${BUCKET}/projects_parquet/YEAR=2012/projects_2012.parquet" \
  "${BUCKET}/projects_parquet/YEAR=2013/projects_2013.parquet" \
  "${BUCKET}/projects_parquet/YEAR=2014/projects_2014.parquet" \
  "${BUCKET}/projects_parquet/YEAR=2015/projects_2015.parquet" \
  "${BUCKET}/projects_parquet/YEAR=2016/projects_2016.parquet" \
  "${BUCKET}/projects_parquet/YEAR=2017/projects_2017.parquet" \
  "${BUCKET}/projects_parquet/YEAR=2018/projects_2018.parquet" \
  "${BUCKET}/projects_parquet/YEAR=2019/projects_2019.parquet" \
  "${BUCKET}/projects_parquet/YEAR=2020/projects_2020.parquet" \
  "${BUCKET}/projects_parquet/YEAR=2021/projects_2021.parquet" \
  "${BUCKET}/projects_parquet/YEAR=2022/projects_2022.parquet" \
  "${BUCKET}/projects_parquet/YEAR=2023/projects_2023.parquet" \
  "${BUCKET}/projects_parquet/YEAR=2024/projects_2024.parquet"

echo "✓ Projects loaded"

# Load ABSTRACTS
echo ""
echo "Loading ABSTRACTS table (all years)..."
bq load --source_format=PARQUET \
  --replace \
  --autodetect \
  ${PROJECT_ID}:${DATASET}.abstracts \
  "${BUCKET}/abstracts_parquet/YEAR=1990/abstracts_1990.parquet" \
  "${BUCKET}/abstracts_parquet/YEAR=1991/abstracts_1991.parquet" \
  "${BUCKET}/abstracts_parquet/YEAR=1992/abstracts_1992.parquet" \
  "${BUCKET}/abstracts_parquet/YEAR=1993/abstracts_1993.parquet" \
  "${BUCKET}/abstracts_parquet/YEAR=1994/abstracts_1994.parquet" \
  "${BUCKET}/abstracts_parquet/YEAR=1995/abstracts_1995.parquet" \
  "${BUCKET}/abstracts_parquet/YEAR=1996/abstracts_1996.parquet" \
  "${BUCKET}/abstracts_parquet/YEAR=1997/abstracts_1997.parquet" \
  "${BUCKET}/abstracts_parquet/YEAR=1998/abstracts_1998.parquet" \
  "${BUCKET}/abstracts_parquet/YEAR=1999/abstracts_1999.parquet" \
  "${BUCKET}/abstracts_parquet/YEAR=2000/abstracts_2000.parquet" \
  "${BUCKET}/abstracts_parquet/YEAR=2001/abstracts_2001.parquet" \
  "${BUCKET}/abstracts_parquet/YEAR=2002/abstracts_2002.parquet" \
  "${BUCKET}/abstracts_parquet/YEAR=2003/abstracts_2003.parquet" \
  "${BUCKET}/abstracts_parquet/YEAR=2004/abstracts_2004.parquet" \
  "${BUCKET}/abstracts_parquet/YEAR=2005/abstracts_2005.parquet" \
  "${BUCKET}/abstracts_parquet/YEAR=2006/abstracts_2006.parquet" \
  "${BUCKET}/abstracts_parquet/YEAR=2007/abstracts_2007.parquet" \
  "${BUCKET}/abstracts_parquet/YEAR=2008/abstracts_2008.parquet" \
  "${BUCKET}/abstracts_parquet/YEAR=2009/abstracts_2009.parquet" \
  "${BUCKET}/abstracts_parquet/YEAR=2010/abstracts_2010.parquet" \
  "${BUCKET}/abstracts_parquet/YEAR=2011/abstracts_2011.parquet" \
  "${BUCKET}/abstracts_parquet/YEAR=2012/abstracts_2012.parquet" \
  "${BUCKET}/abstracts_parquet/YEAR=2013/abstracts_2013.parquet" \
  "${BUCKET}/abstracts_parquet/YEAR=2014/abstracts_2014.parquet" \
  "${BUCKET}/abstracts_parquet/YEAR=2015/abstracts_2015.parquet" \
  "${BUCKET}/abstracts_parquet/YEAR=2016/abstracts_2016.parquet" \
  "${BUCKET}/abstracts_parquet/YEAR=2017/abstracts_2017.parquet" \
  "${BUCKET}/abstracts_parquet/YEAR=2018/abstracts_2018.parquet" \
  "${BUCKET}/abstracts_parquet/YEAR=2019/abstracts_2019.parquet" \
  "${BUCKET}/abstracts_parquet/YEAR=2020/abstracts_2020.parquet" \
  "${BUCKET}/abstracts_parquet/YEAR=2021/abstracts_2021.parquet" \
  "${BUCKET}/abstracts_parquet/YEAR=2022/abstracts_2022.parquet" \
  "${BUCKET}/abstracts_parquet/YEAR=2023/abstracts_2023.parquet" \
  "${BUCKET}/abstracts_parquet/YEAR=2024/abstracts_2024.parquet"

echo "✓ Abstracts loaded"

# Load LINKTABLES
echo ""
echo "Loading LINKTABLES table (all years)..."
bq load --source_format=PARQUET \
  --replace \
  --autodetect \
  ${PROJECT_ID}:${DATASET}.linktables \
  "${BUCKET}/linktables_parquet/YEAR=1990/linktables_1990.parquet" \
  "${BUCKET}/linktables_parquet/YEAR=1991/linktables_1991.parquet" \
  "${BUCKET}/linktables_parquet/YEAR=1992/linktables_1992.parquet" \
  "${BUCKET}/linktables_parquet/YEAR=1993/linktables_1993.parquet" \
  "${BUCKET}/linktables_parquet/YEAR=1994/linktables_1994.parquet" \
  "${BUCKET}/linktables_parquet/YEAR=1995/linktables_1995.parquet" \
  "${BUCKET}/linktables_parquet/YEAR=1996/linktables_1996.parquet" \
  "${BUCKET}/linktables_parquet/YEAR=1997/linktables_1997.parquet" \
  "${BUCKET}/linktables_parquet/YEAR=1998/linktables_1998.parquet" \
  "${BUCKET}/linktables_parquet/YEAR=1999/linktables_1999.parquet" \
  "${BUCKET}/linktables_parquet/YEAR=2000/linktables_2000.parquet" \
  "${BUCKET}/linktables_parquet/YEAR=2001/linktables_2001.parquet" \
  "${BUCKET}/linktables_parquet/YEAR=2002/linktables_2002.parquet" \
  "${BUCKET}/linktables_parquet/YEAR=2003/linktables_2003.parquet" \
  "${BUCKET}/linktables_parquet/YEAR=2004/linktables_2004.parquet" \
  "${BUCKET}/linktables_parquet/YEAR=2005/linktables_2005.parquet" \
  "${BUCKET}/linktables_parquet/YEAR=2006/linktables_2006.parquet" \
  "${BUCKET}/linktables_parquet/YEAR=2007/linktables_2007.parquet" \
  "${BUCKET}/linktables_parquet/YEAR=2008/linktables_2008.parquet" \
  "${BUCKET}/linktables_parquet/YEAR=2009/linktables_2009.parquet" \
  "${BUCKET}/linktables_parquet/YEAR=2010/linktables_2010.parquet" \
  "${BUCKET}/linktables_parquet/YEAR=2011/linktables_2011.parquet" \
  "${BUCKET}/linktables_parquet/YEAR=2012/linktables_2012.parquet" \
  "${BUCKET}/linktables_parquet/YEAR=2013/linktables_2013.parquet" \
  "${BUCKET}/linktables_parquet/YEAR=2014/linktables_2014.parquet" \
  "${BUCKET}/linktables_parquet/YEAR=2015/linktables_2015.parquet" \
  "${BUCKET}/linktables_parquet/YEAR=2016/linktables_2016.parquet" \
  "${BUCKET}/linktables_parquet/YEAR=2017/linktables_2017.parquet" \
  "${BUCKET}/linktables_parquet/YEAR=2018/linktables_2018.parquet" \
  "${BUCKET}/linktables_parquet/YEAR=2019/linktables_2019.parquet" \
  "${BUCKET}/linktables_parquet/YEAR=2020/linktables_2020.parquet" \
  "${BUCKET}/linktables_parquet/YEAR=2021/linktables_2021.parquet" \
  "${BUCKET}/linktables_parquet/YEAR=2022/linktables_2022.parquet" \
  "${BUCKET}/linktables_parquet/YEAR=2023/linktables_2023.parquet" \
  "${BUCKET}/linktables_parquet/YEAR=2024/linktables_2024.parquet"

echo "✓ Link tables loaded"

# Verify
echo ""
echo "======================================================================"
echo "Verifying..."
echo "======================================================================"
echo ""

bq query --use_legacy_sql=false --format=pretty \
"SELECT 
  'projects' as table_name,
  COUNT(*) as rows
FROM \`${PROJECT_ID}.${DATASET}.projects\`"

bq query --use_legacy_sql=false --format=pretty \
"SELECT 
  'abstracts' as table_name,
  COUNT(*) as rows
FROM \`${PROJECT_ID}.${DATASET}.abstracts\`"

bq query --use_legacy_sql=false --format=pretty \
"SELECT 
  'linktables' as table_name,
  COUNT(*) as rows  
FROM \`${PROJECT_ID}.${DATASET}.linktables\`"

echo ""
echo "✓ LOAD COMPLETE!"
