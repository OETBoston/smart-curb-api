from smart_curb_db import SmartCurbDB
from typing import Dict, Any, Optional
import pandas as pd
import logging
logger = logging.getLogger(__name__)


# function name and schema parameter:
# - Suggest a function name `read_api_data` since this is reading data from the API tables
# - Add a required parameter for the database name and schema rather than hardcoding.
def read_public_cds_schema() -> Dict[str, Any]:
    """
    Acquires data from the public cds schema.
    Returns:
        dict: Dictionary of DataFrames from the public cds schema.
    """

    # See notes about using a re-usable function to do the data 
    # table reads.

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


# Suggest separating out into two functions, one to get a job ID,  
# and another to read the data.
#
# The job ID function would be new, and the read_data function could just re-use
# a function suggested above, probably adding an optional filter parameter for job_id.
#
# Design question: Is it ok to omit the job ID and just run with the
# latest, or should we require explicit definition of job_id?
# Using the last job_id makes an assumption that could become out of date if someone
# or something else runs a new job that's not what we wanted to use.

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
            print(f"No Job ID provided. Using latest: {job_id}") # Do we want to default to the last job, or require specification of a job id?
        df_curb_segments = db.get_data("curb_segments")
        df_curb_segment_policies = db.get_data("curb_segment_policies", filter=f"job_id = '{job_id}'")

    return {
        'df_curb_segments': df_curb_segments,
        'df_curb_segment_policies': df_curb_segment_policies,
        'job_id': job_id
    }



# Suggest writing something like this and calling it with a list of table names and the optional job_id filter.
# This could (should?) be part of the shared database connector.

def read_db_tables(dbname: str, schema: str, tables: list[str], filter: str | None = None) -> dict[str, pd.DataFrame]: 
    """TODO: add a docstring"""
    results = {}
    with SmartCurbDB(dbname=dbname, schema=schema) as db:
        for table_name in tables:
            try:
                results[f"df_{table_name}"] = db.get_data(table_name, filter=filter)
            except Exception as e:
                logger.exception("Error reading data from %s", table_name)
                raise

    return(results)