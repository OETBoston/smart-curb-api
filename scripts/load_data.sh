#!/bin/bash

# Configuration
# Update these variables to match your local environment
DB_NAME="smart_curb_db"
DB_USER="postgres"
DATA_DIR="../test-data"
# DB_HOST="localhost" # Uncomment and add -h $DB_HOST to psql commands if needed

sudo -u $DB_USER psql -d $DB_NAME -c "\copy curb_zones FROM '$DATA_DIR/curb_zones.csv' WITH (FORMAT csv, HEADER true);"
#sudo -u $DB_USER psql -d $DB_NAME -c "\copy curb_policy_colors FROM '$DATA_DIR/curb_policy_colors.csv' WITH (FORMAT csv, HEADER true);"
sudo -u $DB_USER psql -d $DB_NAME -c "\copy curb_policies FROM '$DATA_DIR/curb_policies.csv' WITH (FORMAT csv, HEADER true);"
sudo -u $DB_USER psql -d $DB_NAME -c "\copy curb_zone_policies FROM '$DATA_DIR/curb_zone_policies.csv' WITH (FORMAT csv, HEADER true);"
sudo -u $DB_USER psql -d $DB_NAME -c "\copy curb_policy_rules FROM '$DATA_DIR/curb_policy_rules.csv' WITH (FORMAT csv, HEADER true);"
sudo -u $DB_USER psql -d $DB_NAME -c "\copy curb_policy_time_spans FROM '$DATA_DIR/curb_policy_time_spans.csv' WITH (FORMAT csv, HEADER true);"