import json
import uuid
import argparse
import pandas as pd
from shapely import wkb
import geopandas as gpd
from dotenv import load_dotenv
from smart_curb_db import SmartCurbDB


def process_curb_updates(job_id=None):
    """Processes curb segment data from staging to public schema and exports to CSV.

    This function reads curb segment policies from the staging schema, and curb zone policies
    from the public schema. It processes new or updated segments, and flattens nested policy JSONs
    into relational tables. The final results are saved as CSV files.

    Returns:
        None
    """

    load_dotenv()

    # --- 1. Data Acquisition ---
    # Read API Database tables
    with SmartCurbDB(dbname="cds", schema="public_cds") as db:
        df_curb_zones = db.get_data("curb_zones", geom_col="geometry")
        df_curb_policies = db.get_data("curb_policies")
        df_curb_zone_policies = db.get_data("curb_zone_policies")
        df_curb_policy_rules = db.get_data("curb_policy_rules")
        df_curb_policy_time_spans = db.get_data("curb_policy_time_spans")

    # Read Staging Database tables
    with SmartCurbDB(dbname="cds", schema="staging") as db:
        # If no job_id provided, find the most recent one
        if not job_id:
            df_jobs = db.get_data("policy_handling_jobs")
            if df_jobs.empty:
                print("No jobs found in policy_handling_jobs. Exiting.")
                return
            job_id = df_jobs['job_id'].iloc[-1]
            print(f"No Job ID provided. Using latest: {job_id}")
        else:
            print(f"Processing specific Job ID: {job_id}")

        df_curb_segments = db.get_data("curb_segments")
        df_curb_segment_policies = db.get_data("curb_segment_policies", filter=f"job_id = '{job_id}'")

    if df_curb_segment_policies.empty:
        print(f"No records found for job_id: {job_id}")
        return

    # Merge staging data
    df_updates = pd.merge(
        df_curb_segment_policies[['segment_id', 'policy_list']],
        df_curb_segments[['segment_id', 'run_date', 'geography']],
        on='segment_id',
        how='left')

    # --- 2. Processing Setup ---
    new_zones_list = []
    zone_policy_records = []
    policy_records = []
    policy_rule_records = []
    time_span_records = []

    # Get a set of existing IDs for fast lookup
    existing_zone_ids = set(df_curb_zones['curb_zone_id'].unique())

    # --- 3. Main Processing Loop ---
    for _, row in df_updates.iterrows():
        segment_id = row['segment_id']
        policy_list = row['policy_list']
        run_date = row['run_date']

        if segment_id not in existing_zone_ids:
            geom = wkb.loads(row['geography'], hex=True)
            new_zones_list.append({
                'curb_zone_id': segment_id,
                'geometry': geom,
                'published_date': run_date,
                'last_updated_date': run_date
            })
        else:
            # Existing Zone: Update timestamp using .loc
            df_curb_zones.loc[df_curb_zones['curb_zone_id'] == segment_id, 'last_updated_date'] = run_date

        # Clear existing policy associations for this segment
        mask = df_curb_zone_policies['curb_zone_id'] == segment_id
        current_policy_ids = df_curb_zone_policies.loc[mask, 'curb_policy_id'].tolist()
        df_curb_zone_policies = df_curb_zone_policies[~mask]

        df_curb_policies = df_curb_policies[~df_curb_policies['curb_policy_id'].isin(current_policy_ids)]
        df_curb_policy_rules = df_curb_policy_rules[~df_curb_policy_rules['curb_policy_id'].isin(current_policy_ids)]
        df_curb_policy_time_spans = df_curb_policy_time_spans[~df_curb_policy_time_spans['curb_policy_id'].isin(current_policy_ids)]

        # Process the policy_list (dict)
        for priority, policy_str in policy_list.items():
            policy_id = str(uuid.uuid4())

            zone_policy_records.append({
                'curb_zone_id': segment_id,
                'curb_policy_id': policy_id
            })

            policy_records.append({
                'curb_policy_id': policy_id,
                'published_date': run_date,
                'priority': int(priority),
            })

            if policy_str == 'NPA':
                continue

            policy_data = json.loads(policy_str)

            # Extract Rules
            for rule in policy_data.get('rules', []):
                policy_rule_records.append({
                    'rule_id': str(uuid.uuid4()),
                    'curb_policy_id': policy_id,
                    'activity': rule.get('activity'),
                    'max_stay': rule.get('max_stay'),
                    'max_stay_unit': rule.get('max_stay_unit'),
                    'no_return': rule.get('no_return'),
                    'no_return_unit': rule.get('no_return_unit'),
                    'user_classes': rule.get('user_classes'),
                    'user_classes_except': rule.get('user_classes_except'),
                    'purposes': rule.get('purposes')
                })

            # Extract Time Spans
            for ts in policy_data.get('time_spans', []):
                time_span_records.append({
                    'time_span_id': str(uuid.uuid4()),
                    'curb_policy_id': policy_id,
                    'start_date': ts.get('start_date'),
                    'end_date': ts.get('end_date'),
                    'days_of_week': ts.get('days_of_week'),
                    'time_of_day_start': ts.get('time_of_day_start'),
                    'time_of_day_end': ts.get('time_of_day_end'),
                    # ... add other fields as needed
                })

    # --- 4. Final Assembly & Export ---
    # Append new zones to the main GeoDataFrame
    if new_zones_list:
        new_zones_df = gpd.GeoDataFrame(new_zones_list, crs=df_curb_zones.crs)
        df_curb_zones = pd.concat([df_curb_zones, new_zones_df], ignore_index=True)

    # Convert collected lists to DataFrames and concat
    df_curb_zone_policies = pd.concat([df_curb_zone_policies, pd.DataFrame(zone_policy_records)], ignore_index=True)
    df_curb_policies = pd.concat([df_curb_policies, pd.DataFrame(policy_records)], ignore_index=True)
    df_curb_policy_rules = pd.concat([df_curb_policy_rules, pd.DataFrame(policy_rule_records)], ignore_index=True)
    df_curb_policy_time_spans = pd.concat([df_curb_policy_time_spans, pd.DataFrame(time_span_records)],
                                          ignore_index=True)

    # Export to CSV
    df_curb_zones.to_csv('data/curb_zones.csv', index=False)
    df_curb_policies.to_csv('data/curb_policies.csv', index=False)
    df_curb_zone_policies.to_csv('data/curb_zone_policies.csv', index=False)
    df_curb_policy_rules.to_csv('data/curb_policy_rules.csv', index=False)
    df_curb_policy_time_spans.to_csv('data/curb_policy_time_spans.csv', index=False)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Process curb policy updates for a specific Job ID.")
    parser.add_argument("--job-id", type=str, help="The policy handling job_id.")

    args = parser.parse_args()
    process_curb_updates(job_id=args.job_id)