#!/bin/bash
set -euxo pipefail
set -x
set -e

# Environment variables for this file are now set here
export REPORTS_HISTORY=$(mktemp -d --suffix='.history')
export BASE_REPORT="$REPORTS_HISTORY/report.csv"

# Get base report from sv-tests master run
git clone https://github.com/silimate/sv-tests-pvt-results.git --depth 120 $REPORTS_HISTORY

# Delete headers from all report.csv
for file in $(find ./out/report_* -name "*.csv" -print); do
	sed -i.backup 1,1d $file
done

# concatenate test reports
cat $(find ./out/report_* -name "*.csv" -print) >> $COMPARE_REPORT

# Insert header at the first line of concatenated report
sed -i 1i\ $(head -1 $(find ./out/report_* -name "*.csv.backup" -print -quit)) $COMPARE_REPORT

python3 $ANALYZER $COMPARE_REPORT $BASE_REPORT -o $CHANGES_SUMMARY_JSON -t $CHANGES_SUMMARY_MD

# generate history graph
python3 $GRAPHER -n 120 -r $REPORTS_HISTORY

set +e
set +x
