# TierD-2 Evidence Requirements (Cycle 075)

## V-1 Live data collection
- Successful controlled `collect-live` run against Fiverr
- Saved dataset with non-zero records
- Run metadata (timestamp, keyword set, session status, error summary)

## V-2 Live parsing
- Parsed outputs generated from V-1 dataset
- Schema-valid parsed records with pass/fail counts
- Error sample log for failed parses

## V-3 Live scoring
- Full scoring execution on live-collected parsed data
- Score outputs persisted and sanity-checked against expected ranges
- Golden-anchor comparison evidence (including kw=110 reference)

## V-4 Competition score validation
- Competition component validated on live sample
- Metric-level pass criteria documented

## V-5 Opportunity score validation
- Opportunity scores calculated and reviewed on live sample
- Consistency checks across multiple records

## V-6 Feasibility validation
- Feasibility score pipeline run on live sample
- Validation notes proving expected behavior

## V-7 Recommendations generation
- Recommendation generation completes from live-scored inputs
- Output quality checks recorded

## V-8 Dashboard/UI rendering
- Dashboard/export renders live-backed results
- Evidence captures successful render/export path

## V-9 End-to-end validation
- Full path: search -> collection -> parsing -> scoring -> recommendation
- Final artifact proving all prior stages integrate successfully
