-- This is a set of example commands that can be used to load CSV data via psql
\copy curb_zones FROM '../test-data/curb_zones.csv' WITH (FORMAT csv, HEADER true);
\copy curb_policy_colors FROM '../test-data/curb_policy_colors.csv' WITH (FORMAT csv, HEADER true);
\copy curb_policies FROM '../test-data/curb_policies.csv' WITH (FORMAT csv, HEADER true);
\copy curb_zone_policies FROM '../test-data/curb_zone_policies.csv' WITH (FORMAT csv, HEADER true);
\copy curb_policy_rules FROM '../test-data/curb_policy_rules.csv' WITH (FORMAT csv, HEADER true);
\copy curb_policy_time_spans FROM '../test-data/curb_policy_time_spans.csv' WITH (FORMAT csv, HEADER true);