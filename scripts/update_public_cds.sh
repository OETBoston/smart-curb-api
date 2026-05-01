#!/bin/bash

# Configuration
# Update these variables to match your local environment
DB_NAME="smart_curb_db"
DB_USER="postgres"
SQL_DIR="../sql"
# DB_HOST="localhost" # Uncomment and add -h $DB_HOST to psql commands if needed

# Run the update_public_cds.sql script
sudo -u $DB_USER psql -d $DB_NAME -f "$SQL_DIR/update_public_cds.sql"
