import os
from typing import Dict
import logging


def export_to_csv(processed_dict: Dict[str, any], out_dir: str = 'data') -> None:
    """
    Exports processed DataFrames to CSV files in the specified directory.

    Args:
        processed_dict (dict): Dictionary of processed DataFrames.
        out_dir (str): Output directory for CSV files.
    """
    os.makedirs(out_dir, exist_ok=True)
    for key, df in processed_dict.items():
        if hasattr(df, 'to_csv'):
            csv_path = os.path.join(out_dir, f"{key}.csv")
            df.to_csv(csv_path, index=False)
            logging.info(f"Exported {csv_path}")
