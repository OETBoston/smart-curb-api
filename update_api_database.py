"""
update_api_database.py

Main entry point for processing curb policy updates.
"""
import argparse
import logging
import os
from utils import read_public_cds_schema, read_staging_schema, process_updates, export_to_csv
from dotenv import load_dotenv

load_dotenv()

# Good including logging and setting up a format.
# For actual logging, we should use
# logger = logging.getLogger(__name__)
# and then use logger.info("message")
# This will allow logger settings to be taken care of externally as we 
# combine the different parts

logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s')

# Recommend including database name and schema as required args to main, 
# and passing them through when reading data.
#
# See notes elsewhere about job_id being optional or required.
#
# Need to use type of str | None for job_id if we keep it optional.
def main(job_id: str = None) -> None:
    """
    Orchestrates curb policy update processing and CSV export.
    Args:
        job_id (str, optional): The policy handling job_id to use.
    """
    public_cds_data_dict = read_public_cds_schema()
    staging_data_dict = read_staging_schema(job_id=job_id)

    if staging_data_dict is None:
        logging.warning("No jobs found in policy_handling_jobs. Exiting.")
        return

    used_job_id = staging_data_dict['job_id']
    if staging_data_dict['df_curb_segment_policies'].empty:
        logging.warning(f"No records found for job_id: {used_job_id}.")
        return

    processed = process_updates(public_cds_data_dict, staging_data_dict)
    if processed is None:
        logging.warning(f"No records found for job_id: {used_job_id}")
        return

    # Ensure output directory exists
    out_dir = 'data'
    os.makedirs(out_dir, exist_ok=True)
    export_to_csv(processed, out_dir=out_dir)
    logging.info(f"Processed and exported data for job_id: {used_job_id}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Process curb policy updates for a specific Job ID.")
    parser.add_argument("--job-id", type=str, help="The policy handling job_id.")
    args = parser.parse_args()
    main(job_id=args.job_id)
