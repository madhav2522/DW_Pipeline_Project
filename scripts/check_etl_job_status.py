#!/usr/bin/env python3
"""
check_etl_job_status.py
Checks the status of an AWS Glue job run and prints failure details + log pointers.

Defaults:
  - Reads JobRunId from last_glue_run_id.txt if --run-id is not provided
  - JobName defaults to 'myproject-glue-etl'

Usage:
  python3 check_etl_job_status.py
  python3 check_etl_job_status.py --run-id <JobRunId>
"""

import argparse
import sys
from pathlib import Path
import urllib.parse

import boto3
import botocore

DEFAULT_JOB_NAME = "myproject-glue-etl"
RUN_ID_FILE = Path("last_glue_run_id.txt")
AWS_REGION = "us-east-2"  # keep this consistent with your Terraform region


def load_run_id_from_file() -> str:
    if RUN_ID_FILE.exists():
        return RUN_ID_FILE.read_text(encoding="utf-8").strip()
    print(f"[ERROR] No run ID provided and {RUN_ID_FILE} not found.", file=sys.stderr)
    sys.exit(2)


def glue_console_url(job_name: str, run_id: str) -> str:
    # Handy deep-link to the specific job run in the console (optional to use)
    q = urllib.parse.quote
    return (f"https://{AWS_REGION}.console.aws.amazon.com/gluestudio/home?region={AWS_REGION}"
            f"#/job/{q(job_name)}/run/{q(run_id)}")


def cloudwatch_console_url(log_group: str, log_stream: str | None) -> str:
    base = f"https://{AWS_REGION}.console.aws.amazon.com/cloudwatch/home?region={AWS_REGION}#logsV2:log-groups/log-group/{urllib.parse.quote(log_group, safe='')}"
    if log_stream:
        return f"{base}/log-events/{urllib.parse.quote(log_stream, safe='')}"
    return base


def main():
    parser = argparse.ArgumentParser(description="Check AWS Glue ETL job run status.")
    parser.add_argument("--job-name", default=DEFAULT_JOB_NAME, help="Glue job name")
    parser.add_argument("--run-id", default=None, help="Glue JobRunId")
    args = parser.parse_args()

    run_id = args.run_id or load_run_id_from_file()

    glue = boto3.client("glue")
    try:
        resp = glue.get_job_run(JobName=args.job_name, RunId=run_id, PredecessorsIncluded=False)
        jr = resp["JobRun"]
        status = jr.get("JobRunState")
        error_msg = jr.get("ErrorMessage")
        log_group = jr.get("LogGroupName") or "/aws-glue/jobs/output"
        # Some Glue versions set LogStreamName; if missing, we’ll still give the group
        log_stream = jr.get("LogStreamName")

        print(f"Glue job '{args.job_name}' run {run_id} status: {status}")
        if status in ("FAILED", "TIMEOUT"):
            print("\n--- Failure details ---")
            if error_msg:
                print(error_msg)
            else:
                print("(No ErrorMessage field from Glue; check CloudWatch logs.)")

            print("\n--- Logs ---")
            print(f"CloudWatch group : {log_group}")
            if log_stream:
                print(f"CloudWatch stream: {log_stream}")
            print(f"Open (optional): {cloudwatch_console_url(log_group, log_stream)}")
            print(f"Glue run (optional): {glue_console_url(args.job_name, run_id)}")
            sys.exit(1)
    except botocore.exceptions.ClientError as e:
        print(f"[ERROR] AWS Glue error: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"[ERROR] Unexpected error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
