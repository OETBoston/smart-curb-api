"""
curb_processors.py

Contains modular functions for curb data acquisition, processing, and export.
"""
import json
import uuid
import pandas as pd
from shapely import wkb
import geopandas as gpd
from typing import Dict, Any, Optional

# don't use Any. Instead, use Dict[str, pd.DataFrame]
# Prefer use of mytype | None over Optional[mytype]
# Result should probably not be optional, but instead raise on error.
# (Design discussion: Python practice tends towards raise on error rather than return None and check for None, 
# but either can work.)
def process_updates(public_cds_data_dict: Dict[str, Any], staging_data_dict: Dict[str, Any]) -> Optional[Dict[str, pd.DataFrame]]:
    """
    Processes and flattens the data, returning updated DataFrames.

    Args:
        public_cds_data_dict (dict): DataFrames from public_cds schema.
        staging_data_dict (dict): DataFrames from staging schema.

    Returns:
        dict: Updated DataFrames or None if no updates.
    """
    df_curb_zones = public_cds_data_dict['df_curb_zones']
    df_curb_policies = public_cds_data_dict['df_curb_policies']
    df_curb_zone_policies = public_cds_data_dict['df_curb_zone_policies']
    df_curb_policy_rules = public_cds_data_dict['df_curb_policy_rules']
    df_curb_policy_time_spans = public_cds_data_dict['df_curb_policy_time_spans']

    df_curb_segments = staging_data_dict['df_curb_segments']
    df_curb_segment_policies = staging_data_dict['df_curb_segment_policies']

    if df_curb_segment_policies.empty:
        return None # See note about returning None vs. raising

    # This is fine, especially since the db connector doesn't provide
    # an ability to use a joined query.  BUT- either adding this 
    # capability or adding a view could be an option.
    #
    # pd.merge is probably fine and fast enough, but can be memory 
    # intensive if the tables get large.
    #
    # If we keep pd.merge, consider deleting the source tables
    # to manage memory use.
    df_updates = pd.merge(
        df_curb_segment_policies[['segment_id', 'policy_list']],
        df_curb_segments[['segment_id', 'run_date', 'geography']],
        on='segment_id', how='left')

    new_zones_list = []
    zone_policy_records = []
    policy_records = []
    policy_rule_records = []
    time_span_records = []
    existing_zone_ids = set(df_curb_zones['curb_zone_id'].unique())

    for _, row in df_updates.iterrows():
        segment_id = row['segment_id']

        # The database docs don't define policy_list, but rather 
        # a table with segment_id and policy. it was expected that segments with 
        # multiple polices would be repeated. Example:
        #
        # | segment_id | policy_id |
        # |------------|-----------|
        # | 1          | 1001      |
        # | 1          | 1002      |
        #
        # Instead, curb_segment_policies has a json dict of policies, formatted
        # as {"0": {policy __string__}, ...}
        #
        # That seems fine, so we should update the staging db docs.
        # We should replace the policy string with policy json (I think 
        # I've heard discussion about this)
        #
        #

        policy_list = row['policy_list'] 
        run_date = row['run_date']

        # Interpretation: This section checks to see if a segment_id matches an existing zone_id. 
        # No? Add a new zone.
        # Yes? Update last updated date for the zone.

        # Not sure if segment_ids should become zone_ids - these are different concepts.
        # Could be ok if segment IDs will always be constant until segments change.
        # BUT - we need to combine segments with like policies somewhere. Does that fit with this scheme?
        #       Maybe the first encountered segment_id?
        #
        # FOR NOW - we may want to just worry about creating new CDS, then tackle replacing 
        # changed zones (probably based on blockface ID) at a later time.

        if segment_id not in existing_zone_ids: 
            geom = wkb.loads(row['geography'], hex=True)
            new_zones_list.append({
                'curb_zone_id': segment_id,
                'geometry': geom,
                'published_date': run_date,
                'last_updated_date': run_date
            })
        else:
            df_curb_zones.loc[df_curb_zones['curb_zone_id'] == segment_id, 'last_updated_date'] = run_date


        # Interpretation:
        # - Get a list of policy IDs associated with this segment. Policy IDs are from CDS.
        # - Remove those policies from the CDF curb_zone policies table (merge table)
        # - Remove those polices from the CDF policies table. Does the same with rules and timespans.
        # Comments:
        # - Hard to parse w/o comments.
        # - Problem if policies are normalized and used on multiple segments.
        # - Same issue if rules and timespans are normalized.

        mask = df_curb_zone_policies['curb_zone_id'] == segment_id
        current_policy_ids = df_curb_zone_policies.loc[mask, 'curb_policy_id'].tolist()
        df_curb_zone_policies = df_curb_zone_policies[~mask]
        df_curb_policies = df_curb_policies[~df_curb_policies['curb_policy_id'].isin(current_policy_ids)]
        df_curb_policy_rules = df_curb_policy_rules[~df_curb_policy_rules['curb_policy_id'].isin(current_policy_ids)]
        df_curb_policy_time_spans = df_curb_policy_time_spans[~df_curb_policy_time_spans['curb_policy_id'].isin(current_policy_ids)]


        # IDE not recognizing .items means we need to add type hints.
        # This needs to happen where policy list is assigned, something 
        # like (simple, could add more detail about schema):
        # from typing import cast, Dict
        # policy_list = cast(Dict[str, dict], row["policy_list"])
        for priority, policy_str in policy_list.items(): 

            # If we put this in a function like assign_policy(...), we can 
            # later expand that function to also de-duplicate as it adds.
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
            if policy_str == 'NPA': # need to remove since we've replaced this elsewhere.
                continue

            # policy_str should be a dict already. We should not need to convert from json.  
            # The policy list should probably be storing json instead of stringified json.
            policy_data = json.loads(policy_str)

            #Suggest separate functions for rule and timespan addition as well, likely 
            # called from the function that adds a policy.
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
            for ts in policy_data.get('time_spans', []):
                time_span_records.append({
                    'time_span_id': str(uuid.uuid4()),
                    'curb_policy_id': policy_id,
                    'start_date': ts.get('start_date'),
                    'end_date': ts.get('end_date'),
                    'days_of_week': ts.get('days_of_week'),
                    'time_of_day_start': ts.get('time_of_day_start'),
                    'time_of_day_end': ts.get('time_of_day_end'),
                })


    # Interpretation:
    # - Add new zones if there are new zones
    # - Add new policies, rules, and time_spans
    #  (Assuming this is done here for performance rather than concating in the loop)

    if new_zones_list:
        new_zones_df = gpd.GeoDataFrame(new_zones_list, crs=df_curb_zones.crs)
        df_curb_zones = pd.concat([df_curb_zones, new_zones_df], ignore_index=True)
    df_curb_zone_policies = pd.concat([df_curb_zone_policies, pd.DataFrame(zone_policy_records)], ignore_index=True)
    df_curb_policies = pd.concat([df_curb_policies, pd.DataFrame(policy_records)], ignore_index=True)
    df_curb_policy_rules = pd.concat([df_curb_policy_rules, pd.DataFrame(policy_rule_records)], ignore_index=True)
    df_curb_policy_time_spans = pd.concat([df_curb_policy_time_spans, pd.DataFrame(time_span_records)], ignore_index=True)

    # Returns modified CS dataframes.
    return {
        'df_curb_zones': df_curb_zones,
        'df_curb_policies': df_curb_policies,
        'df_curb_zone_policies': df_curb_zone_policies,
        'df_curb_policy_rules': df_curb_policy_rules,
        'df_curb_policy_time_spans': df_curb_policy_time_spans
    }

# General comments based on review
#
# - Slightly concerned about just updating CDS dataframes, especially
#   when we update zones. Probably not wrong, but hard to follow and
#   opportunity for error if we change things later.
# - Do we ultimately want to modify the SQL database by dropping and then 
#   appending records, rather than creating the whole DB anew? In a production
#   environment where things are updated frequently, this seems like a better
#   solution.