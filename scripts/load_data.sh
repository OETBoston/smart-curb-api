#!/bin/bash

# Configuration
# Update these variables to match your local environment
DB_NAME="smart_curb_db"
DB_USER="postgres"
# DB_HOST="localhost" # Uncomment and add -h $DB_HOST to psql commands if needed

# Directory containing the CSV files
DATA_DIR="./data"

echo "Loading data into $DB_NAME..."

# 1. Load independent tables first
echo "Loading curb_zones..."
psql -d $DB_NAME -U $DB_USER -c "\copy curb_zones FROM '$DATA_DIR/curb_zones.csv' WITH (FORMAT csv, HEADER true)"

echo "Loading curb_policy_colors..."
psql -d $DB_NAME -U $DB_USER -c "\copy curb_policy_colors FROM '$DATA_DIR/curb_policy_colors.csv' WITH (FORMAT csv, HEADER true)"

# 2. Load tables with dependencies
echo "Loading curb_policies..."
psql -d $DB_NAME -U $DB_USER -c "\copy curb_policies FROM '$DATA_DIR/curb_policies.csv' WITH (FORMAT csv, HEADER true)"

# 3. Load child tables
echo "Loading curb_zone_policies..."
psql -d $DB_NAME -U $DB_USER -c "\copy curb_zone_policies FROM '$DATA_DIR/curb_zone_policies.csv' WITH (FORMAT csv, HEADER true)"

echo "Loading curb_policy_rules..."
psql -d $DB_NAME -U $DB_USER -c "\copy curb_policy_rules FROM '$DATA_DIR/curb_policy_rules.csv' WITH (FORMAT csv, HEADER true)"

echo "Loading curb_policy_time_spans..."
psql -d $DB_NAME -U $DB_USER -c "\copy curb_policy_time_spans FROM '$DATA_DIR/curb_policy_time_spans.csv' WITH (FORMAT csv, HEADER true)"

echo "Data load complete."
