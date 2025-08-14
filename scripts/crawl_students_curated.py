#!/usr/bin/env python3
"""
One-file crawler helper:
- Validates the curated S3 path has data
- (Optional) attaches AWS managed 'service-role/AWSGlueServiceRole' to your Glue role
- Creates/updates the crawler targeting the curated parent path
- Starts the crawler, waits, and prints the reason if it fails (with CloudWatch log tail)
- Lists tables in the Glue database

Usage:
  python3 scripts/crawl_students_curated.py \
    --db myproject_db \
    --crawler students_curated_crawler \
    --role myproject-glue-role \
    --s3 s3://myproject-raw-data-103259692325-us-east-2/curated/students_transformed/ \
    --fix-role
"""
import argparse, os, time, sys, re
import boto3
from botocore.exceptions import ClientError

DEFAULT_DB      = "myproject_db"
DEFAULT_CRAWLER = "students_curated_crawler"
DEFAULT_ROLE    = "myproject-glue-role"
DEFAULT_REGION  = os.getenv("AWS_REGION", "us-east-2")
GLUE_SERVICE_ROLE_ARN = "arn:aws:iam::aws:policy/service-role/AWSGlueServiceRole"

def parse_s3_url(url: str):
    m = re.match(r"s3://([^/]+)/?(.*)", url.strip())
    if not m:
        raise ValueError(f"Invalid S3 URL: {url}")
    bucket, prefix = m.group(1), m.group(2)
    # Ensure prefix ends with "/" for folder targets
    if prefix and not prefix.endswith("/"):
        prefix += "/"
    return bucket, prefix

def s3_has_objects(s3, bucket, prefix) -> bool:
    try:
        resp = s3.list_objects_v2(Bucket=bucket, Prefix=prefix, MaxKeys=5)
        found = [o["Key"] for o in resp.get("Contents", [])]
        if found:
            print("✅ Found objects under", f"s3://{bucket}/{prefix}")
            for k in found:
                print("   -", k)
            return True
        else:
            print("⚠️ No objects under", f"s3://{bucket}/{prefix}")
            return False
    except ClientError as e:
        print("❌ S3 access error:", e.response.get("Error", {}).get("Message") or str(e))
        return False

def ensure_database(glue, db_name):
    try:
        glue.get_database(Name=db_name)
        print(f"✅ Using existing Glue database: {db_name}")
    except glue.exceptions.EntityNotFoundException:
        glue.create_database(DatabaseInput={"Name": db_name})
        print(f"✅ Created Glue database: {db_name}")

def ensure_role_policy(iam, role_name, attach: bool):
    # Check if AWSGlueServiceRole policy is attached; attach if --fix-role specified
    attached = iam.list_attached_role_policies(RoleName=role_name)["AttachedPolicies"]
    has = any(p["PolicyArn"] == GLUE_SERVICE_ROLE_ARN for p in attached)
    if has:
        print(f"✅ Role {role_name} already has AWSGlueServiceRole")
    else:
        msg = f"⚠️ Role {role_name} missing AWSGlueServiceRole"
        if attach:
            iam.attach_role_policy(RoleName=role_name, PolicyArn=GLUE_SERVICE_ROLE_ARN)
            print(f"{msg} → attached now.")
        else:
            print(f"{msg}. Re-run with --fix-role to attach automatically.")

def create_or_update_crawler(glue, name, role, db, s3_path):
    targets = {"S3Targets": [{"Path": s3_path}]}
    try:
        glue.get_crawler(Name=name)
        glue.update_crawler(Name=name, Role=role, DatabaseName=db, Targets=targets)
        print(f"✅ Updated crawler: {name}")
    except glue.exceptions.EntityNotFoundException:
        glue.create_crawler(Name=name, Role=role, DatabaseName=db, Targets=targets)
        print(f"✅ Created crawler: {name}")

def start_and_wait(glue, crawler_name, logs):
    glue.start_crawler(Name=crawler_name)
    print(f"🚀 Started crawler: {crawler_name}")
    last_status = None
    while True:
        c = glue.get_crawler(Name=crawler_name)["Crawler"]
        state = c.get("State")
        last = c.get("LastCrawl", {})
        last_status = last.get("Status")
        print(f"State={state} LastStatus={last_status}")
        if state == "READY":
            break
        time.sleep(8)

    # Print result and helpful diagnostics
    lc = glue.get_crawler(Name=crawler_name)["Crawler"].get("LastCrawl", {})
    status = lc.get("Status")
    err = lc.get("ErrorMessage")
    if status == "SUCCEEDED":
        print("✅ Crawl finished successfully.")
    else:
        print(f"❌ Crawl finished with status: {status or 'UNKNOWN'}")
        if err:
            print("ErrorMessage:", err)
        # Try to tail CloudWatch
        try_tail_cloudwatch(logs, crawler_name)

def try_tail_cloudwatch(logs, crawler_name):
    log_group = "/aws-glue/crawlers"
    try:
        streams = logs.describe_log_streams(
            logGroupName=log_group, orderBy="LastEventTime", descending=True, limit=25
        )["logStreams"]
    except logs.exceptions.ResourceNotFoundException:
        print("(No CloudWatch log group for crawlers found.)")
        return
    # Pick a recent stream that mentions the crawler name
    target = None
    for s in streams:
        if crawler_name in s.get("logStreamName",""):
            target = s["logStreamName"]; break
    if not target and streams:
        target = streams[0]["logStreamName"]

    if not target:
        print("(No relevant CloudWatch log stream found.)")
        return

    print(f"\n--- CloudWatch tail ({log_group} / {target}) ---")
    events = logs.get_log_events(
        logGroupName=log_group, logStreamName=target, limit=200, startFromHead=False
    )["events"]
    for e in events[-80:]:
        print(e["message"].rstrip())
    print("--- end log tail ---\n")

def list_tables(glue, db):
    print("\n📚 Tables in database:", db)
    paginator = glue.get_paginator("get_tables")
    names = []
    for page in paginator.paginate(DatabaseName=db):
        for t in page.get("TableList", []):
            names.append(t["Name"])
    if names:
        for n in sorted(names):
            print(" -", n)
    else:
        print(" (none)")

def main():
    ap = argparse.ArgumentParser(description="Create/Update & run a Glue crawler over curated folder (one file).")
    ap.add_argument("--db", default=DEFAULT_DB)
    ap.add_argument("--crawler", default=DEFAULT_CRAWLER)
    ap.add_argument("--role", default=DEFAULT_ROLE)
    ap.add_argument("--s3", required=True, help="S3 path to curated parent, e.g. s3://.../curated/students_transformed/")
    ap.add_argument("--region", default=DEFAULT_REGION)
    ap.add_argument("--fix-role", action="store_true", help="Attach AWSGlueServiceRole to the role if missing")
    args = ap.parse_args()

    # Clients
    glue = boto3.client("glue", region_name=args.region)
    s3   = boto3.client("s3",   region_name=args.region)
    iam  = boto3.client("iam",  region_name=args.region)
    logs = boto3.client("logs", region_name=args.region)

    # 0) S3 sanity check
    bucket, prefix = parse_s3_url(args.s3)
    if not s3_has_objects(s3, bucket, prefix):
        print("\nFix the S3 path or permissions (needs ListBucket/GetObject) and re-run.")
        sys.exit(2)

    # 1) Role policy check/attach
    ensure_role_policy(iam, args.role, attach=args.fix_role)

    # 2) Ensure DB exists
    ensure_database(glue, args.db)

    # 3) Create/update crawler
    create_or_update_crawler(glue, args.crawler, args.role, args.db, args.s3)

    # 4) Run crawler and wait; show logs if it fails
    start_and_wait(glue, args.crawler, logs)

    # 5) List tables
    list_tables(glue, args.db)

if __name__ == "__main__":
    main()
