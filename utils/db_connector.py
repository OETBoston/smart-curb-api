from smart_curb_db import SmartCurbDB
from typing import Dict, Any, Optional


def read_public_cds_schema() -> Dict[str, Any]:
    """
    Acquires data from the public cds schema.
    Returns:
        dict: Dictionary of DataFrames from the public cds schema.
    """

    # Public schema
    with SmartCurbDB(dbname="cds", schema="public_cds") as db:
        df_curb_zones = db.get_data("curb_zones", geom_col="geometry")
        df_curb_policies = db.get_data("curb_policies")
        df_curb_zone_policies = db.get_data("curb_zone_policies")
        df_curb_policy_rules = db.get_data("curb_policy_rules")
        df_curb_policy_time_spans = db.get_data("curb_policy_time_spans")

    return {
        'df_curb_zones': df_curb_zones,
        'df_curb_policies': df_curb_policies,
        'df_curb_zone_policies': df_curb_zone_policies,
        'df_curb_policy_rules': df_curb_policy_rules,
        'df_curb_policy_time_spans': df_curb_policy_time_spans,
    }


def read_staging_schema(job_id: Optional[str] = None) -> Optional[Dict[str, Any]]:
    """
    Acquires data from the staging schema.
    Returns:
        dict: Dictionary of DataFrames and job_id used.
    """

    # Staging schema
    with SmartCurbDB(dbname="cds", schema="staging") as db:
        if not job_id:
            df_jobs = db.get_data("policy_handling_jobs")
            if df_jobs.empty:
                print("No jobs found in policy_handling_jobs. Exiting.")
                return None
            job_id = df_jobs['job_id'].iloc[-1]
            print(f"No Job ID provided. Using latest: {job_id}")
        df_curb_segments = db.get_data("curb_segments")
        df_curb_segment_policies = db.get_data("curb_segment_policies", filter=f"job_id = '{job_id}'")

    return {
        'df_curb_segments': df_curb_segments,
        'df_curb_segment_policies': df_curb_segment_policies,
        'job_id': job_id
    }