#!/usr/bin/env python3
"""
data_ingestion_to_s3.py
Uploads Students.csv and exams.csv to your RAW S3 bucket using boto3.

- Bucket: myproject-raw-data-103259692325-us-east-2
- Keys:
    students/students.csv
    exams/exams.csv

Usage:
  python3 data_ingestion_to_s3.py
  # or customize file locations:
  python3 data_ingestion_to_s3.py --students ./Students.csv --exams ./exams.csv
"""

import argparse
import os
import sys
import mimetypes
import botocore
import boto3

RAW_BUCKET = "myproject-raw-data-103259692325-us-east-2"
KEY_STUDENTS = "students/students.csv"
KEY_EXAMS = "exams/exams.csv"
AWS_REGION = "us-east-2"  # keep consistent with your Terraform region


def _err(msg: str):
    print(f"[ERROR] {msg}", file=sys.stderr)


def _info(msg: str):
    print(f"[INFO] {msg}")


def _guess_content_type(path: str) -> str:
    ctype, _ = mimetypes.guess_type(path)
    return ctype or "text/csv"


def upload_file(s3_client, local_path: str, bucket: str, key: str):
    if not os.path.isfile(local_path):
        raise FileNotFoundError(f"Local file not found: {local_path}")

    extra_args = {"ContentType": _guess_content_type(local_path)}
    _info(f"Uploading {local_path} -> s3://{bucket}/{key}")
    s3_client.upload_file(local_path, bucket, key, ExtraArgs=extra_args)

    # Sanity check: HEAD the object
    s3_client.head_object(Bucket=bucket, Key=key)
    _info(f"✅ Uploaded: s3://{bucket}/{key}")


def main():
    parser = argparse.ArgumentParser(description="Upload CSVs to S3 (RAW).")
    parser.add_argument("--students", default="./Students.csv",
                        help="Path to Students.csv (default: ./Students.csv)")
    parser.add_argument("--exams", default="./exams.csv",
                        help="Path to exams.csv (default: ./exams.csv)")
    args = parser.parse_args()

    # Create session explicitly with region (works with env/IAM role creds)
    session = boto3.Session(region_name=AWS_REGION)
    s3 = session.client("s3")

    try:
        # Optional: verify bucket exists + you can access it
        s3.head_bucket(Bucket=RAW_BUCKET)
        _info(f"Bucket OK: {RAW_BUCKET}")
    except botocore.exceptions.ClientError as e:
        _err(f"Cannot access bucket '{RAW_BUCKET}'. Error: {e}")
        _err("Make sure your IAM permissions are correct and the bucket name matches Terraform output.")
        sys.exit(1)

    try:
        upload_file(s3, args.students, RAW_BUCKET, KEY_STUDENTS)
        upload_file(s3, args.exams, RAW_BUCKET, KEY_EXAMS)
        _info("All uploads completed 🎯")
        _info(f"Students -> s3://{RAW_BUCKET}/{KEY_STUDENTS}")
        _info(f"Exams    -> s3://{RAW_BUCKET}/{KEY_EXAMS}")
    except FileNotFoundError as e:
        _err(str(e))
        _err("Check the filenames and paths. You can pass custom paths via --students and --exams.")
        sys.exit(1)
    except botocore.exceptions.ClientError as e:
        _err(f"AWS error during upload: {e}")
        sys.exit(1)
    except Exception as e:
        _err(f"Unexpected error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
