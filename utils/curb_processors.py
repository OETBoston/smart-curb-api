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
        return None

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
            df_curb_zones.loc[df_curb_zones['curb_zone_id'] == segment_id, 'last_updated_date'] = run_date
        mask = df_curb_zone_policies['curb_zone_id'] == segment_id
        current_policy_ids = df_curb_zone_policies.loc[mask, 'curb_policy_id'].tolist()
        df_curb_zone_policies = df_curb_zone_policies[~mask]
        df_curb_policies = df_curb_policies[~df_curb_policies['curb_policy_id'].isin(current_policy_ids)]
        df_curb_policy_rules = df_curb_policy_rules[~df_curb_policy_rules['curb_policy_id'].isin(current_policy_ids)]
        df_curb_policy_time_spans = df_curb_policy_time_spans[~df_curb_policy_time_spans['curb_policy_id'].isin(current_policy_ids)]
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
    if new_zones_list:
        new_zones_df = gpd.GeoDataFrame(new_zones_list, crs=df_curb_zones.crs)
        df_curb_zones = pd.concat([df_curb_zones, new_zones_df], ignore_index=True)
    df_curb_zone_policies = pd.concat([df_curb_zone_policies, pd.DataFrame(zone_policy_records)], ignore_index=True)
    df_curb_policies = pd.concat([df_curb_policies, pd.DataFrame(policy_records)], ignore_index=True)
    df_curb_policy_rules = pd.concat([df_curb_policy_rules, pd.DataFrame(policy_rule_records)], ignore_index=True)
    df_curb_policy_time_spans = pd.concat([df_curb_policy_time_spans, pd.DataFrame(time_span_records)], ignore_index=True)
    return {
        'df_curb_zones': df_curb_zones,
        'df_curb_policies': df_curb_policies,
        'df_curb_zone_policies': df_curb_zone_policies,
        'df_curb_policy_rules': df_curb_policy_rules,
        'df_curb_policy_time_spans': df_curb_policy_time_spans
    }
