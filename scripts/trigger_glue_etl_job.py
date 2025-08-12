#!/usr/bin/env python3
"""
trigger_glue_etl_job.py
Starts the Glue ETL job created by Terraform and prints the JobRunId.

Defaults:
  - JobName: myproject-glue-etl
  - TempDir: s3://myproject-raw-data-103259692325-us-east-2/_glue_temp/

Usage:
  python3 trigger_glue_etl_job.py
  # or override:
  python3 trigger_glue_etl_job.py --job-name myproject-glue-etl --temp-dir s3://bucket/_glue_temp/
"""

import argparse
import json
import sys
from pathlib import Path

import boto3
import botocore

DEFAULT_JOB_NAME = "myproject-glue-etl"
DEFAULT_TEMP_DIR = "s3://myproject-raw-data-103259692325-us-east-2/_glue_temp/"
RUN_ID_FILE = Path("last_glue_run_id.txt")


def start_glue_job(job_name: str, temp_dir: str, extra_args: dict | None = None) -> str:
    client = boto3.client("glue")
    args = {
        "--TempDir": temp_dir,
        "--enable-continuous-cloudwatch-log": "true",
        "--enable-metrics": "true",
        "--job-language": "python",
    }
    if extra_args:
        # allow user to pass-through additional Glue arguments (e.g., --students_path etc.)
        args.update(extra_args)

    resp = client.start_job_run(JobName=job_name, Arguments=args)
    return resp["JobRunId"]


def main():
    parser = argparse.ArgumentParser(description="Trigger AWS Glue ETL job.")
    parser.add_argument("--job-name", default=DEFAULT_JOB_NAME, help="Glue job name")
    parser.add_argument("--temp-dir", default=DEFAULT_TEMP_DIR, help="S3 temp dir for Glue")
    parser.add_argument(
        "--extra-args",
        default=None,
        help="JSON dict of extra Glue arguments to pass (e.g. '{\"--key\":\"value\"}')",
    )
    args = parser.parse_args()

    try:
        extra = json.loads(args.extra_args) if args.extra_args else None
    except json.JSONDecodeError as e:
        print(f"[ERROR] --extra-args must be valid JSON: {e}", file=sys.stderr)
        sys.exit(2)

    try:
        run_id = start_glue_job(args.job_name, args.temp_dir, extra)
        print(f"✅ Started Glue job '{args.job_name}'")
        print(f"   JobRunId: {run_id}")
        RUN_ID_FILE.write_text(run_id, encoding="utf-8")
        print(f"   (Saved to {RUN_ID_FILE.resolve()})")
        print("\nNext:")
        print("  python3 check_etl_job_status.py  # use the saved run id")
    except botocore.exceptions.ClientError as e:
        print(f"[ERROR] AWS Glue error: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"[ERROR] Unexpected error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
