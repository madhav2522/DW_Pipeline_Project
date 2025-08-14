#!/usr/bin/env python3
"""
Upload a local file to S3 (multipart + progress).
Usage:
  python3 scripts/upload_large_to_s3.py \
    --file data/students_large.csv \
    --bucket myproject-raw-data-103259692325-us-east-2 \
    --key students/students_large.csv \
    --region us-east-2
"""

import argparse
import os
import sys
import math
import time
import threading
import boto3
from botocore.exceptions import ClientError
from boto3.s3.transfer import TransferConfig

class ProgressPercentage:
    def __init__(self, filename: str):
        self._filename = filename
        self._size = float(os.path.getsize(filename))
        self._seen = 0
        self._lock = threading.Lock()
        self._start = time.time()

    def __call__(self, bytes_amount: int):
        with self._lock:
            self._seen += bytes_amount
            pct = 100.0 if self._size == 0 else (self._seen / self._size) * 100.0
            elapsed = max(time.time() - self._start, 1e-6)
            mbps = (self._seen / (1024 * 1024)) / elapsed
            bar_len = 30
            filled = int(math.floor(bar_len * pct / 100))
            bar = "#" * filled + "-" * (bar_len - filled)
            sys.stdout.write(
                f"\r[{bar}] {pct:6.2f}%  {self._seen/1e6:,.1f}MB/{self._size/1e6:,.1f}MB  {mbps:,.2f} MB/s"
            )
            sys.stdout.flush()
            if self._seen >= self._size:
                sys.stdout.write("\n")

def parse_args():
    p = argparse.ArgumentParser(description="Upload a file to S3 with multipart + progress.")
    p.add_argument("--file", required=True, help="Local file path, e.g. data/students_large.csv")
    p.add_argument("--bucket", required=True, help="S3 bucket name")
    p.add_argument("--key", required=True, help="S3 object key, e.g. students/students_large.csv")
    p.add_argument("--region", default=os.getenv("AWS_REGION") or "us-east-2", help="AWS region")
    return p.parse_args()

def main():
    args = parse_args()

    local_path = os.path.abspath(args.file)
    if not os.path.exists(local_path):
        print(f"ERROR: File not found: {local_path}")
        return 1

    print("Uploading:")
    print(f"  Local : {local_path}")
    print(f"  S3    : s3://{args.bucket}/{args.key}")
    print(f"  Region: {args.region}")

    session = boto3.session.Session(region_name=args.region)
    s3 = session.client("s3")

    config = TransferConfig(
        multipart_threshold=8 * 1024 * 1024,   # 8 MB
        multipart_chunksize=16 * 1024 * 1024,  # 16 MB
        max_concurrency=10,
        use_threads=True,
    )

    extra_args = {
        "ContentType": "text/csv",
        # "ServerSideEncryption": "AES256",  # optional
    }

    try:
        s3.upload_file(
            Filename=local_path,
            Bucket=args.bucket,
            Key=args.key,
            ExtraArgs=extra_args,
            Config=config,
            Callback=ProgressPercentage(local_path),
        )
        head = s3.head_object(Bucket=args.bucket, Key=args.key)
        etag = head.get("ETag", "").strip('"')
        size = head.get("ContentLength", 0)
        print(f"✅ Upload complete. ETag={etag}  Size={size:,} bytes")
        print(f"s3://{args.bucket}/{args.key}")
        return 0
    except ClientError as e:
        print(f"ERROR: {e}")
        return 2

if __name__ == "__main__":
    sys.exit(main())
