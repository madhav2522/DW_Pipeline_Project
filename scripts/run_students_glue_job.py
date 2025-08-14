#!/usr/bin/env python3
import os, time
from datetime import datetime, UTC
import boto3
import snowflake.connector

# ---- config (env-driven) ----
REGION               = os.getenv("AWS_REGION", "us-east-2")
JOB_NAME             = os.getenv("GLUE_JOB_NAME", "myproject-etl")
CRAWLER_NAME         = os.getenv("GLUE_CRAWLER_NAME", "students_curated_crawler")
CATALOG_DB           = os.getenv("GLUE_DB", "myproject_db")
CATALOG_TABLE        = os.getenv("GLUE_TABLE", "students_transformed")

RAW_BUCKET           = os.getenv("RAW_BUCKET", "myproject-raw-data-103259692325-us-east-2")
STUDENTS_KEY         = os.getenv("STUDENTS_KEY", "students/students_large.csv")
CURATED_PREFIX       = os.getenv("CURATED_PREFIX", "curated")

# Snowflake (set as env vars before running)
SF_ACCOUNT   = os.getenv("SNOWFLAKE_ACCOUNT")
SF_USER      = os.getenv("SNOWFLAKE_USER")
SF_PASSWORD  = os.getenv("SNOWFLAKE_PASSWORD")
SF_ROLE      = os.getenv("SNOWFLAKE_ROLE", "ACCOUNTADMIN")
SF_WAREHOUSE = os.getenv("SNOWFLAKE_WAREHOUSE", "COMPUTE_WH")
SF_DATABASE  = os.getenv("SNOWFLAKE_DATABASE", "MY_DB")
SF_SCHEMA    = os.getenv("SNOWFLAKE_SCHEMA", "PUBLIC")

# AWS read creds for the Snowflake stage (read-only is fine)
AWS_READ_KEY    = os.getenv("AWS_READ_KEY")
AWS_READ_SECRET = os.getenv("AWS_READ_SECRET")

def start_glue_job(glue, run_id):
    args = {
        "--RAW_BUCKET": RAW_BUCKET,
        "--STUDENTS_KEY": STUDENTS_KEY,
        "--CURATED_PREFIX": CURATED_PREFIX,
        "--RUN_ID": run_id,
    }
    resp = glue.start_job_run(JobName=JOB_NAME, Arguments=args)
    return resp["JobRunId"]

def wait_glue_job(glue, run_id):
    while True:
        r = glue.get_job_run(JobName=JOB_NAME, RunId=run_id, PredecessorsIncluded=False)
        state = r["JobRun"]["JobRunState"]
        print("Glue job state:", state)
        if state in ("SUCCEEDED","FAILED","STOPPED","TIMEOUT","ERROR"):
            return state
        time.sleep(10)

def start_and_wait_crawler(glue):
    glue.start_crawler(Name=CRAWLER_NAME)
    print("Crawler started:", CRAWLER_NAME)
    while True:
        c = glue.get_crawler(Name=CRAWLER_NAME)["Crawler"]
        state = c.get("State")
        last  = c.get("LastCrawl", {})
        print("Crawler state:", state, "LastStatus:", last.get("Status"))
        if state == "READY":
            return last.get("Status")
        time.sleep(8)

def latest_partition_location(glue):
    # Fetch all partitions and pick the max run value
    parts = []
    token = None
    while True:
        kwargs = dict(DatabaseName=CATALOG_DB, TableName=CATALOG_TABLE)
        if token: kwargs["NextToken"] = token
        res = glue.get_partitions(**kwargs)
        for p in res.get("Partitions", []):
            run_val = p["Values"][0]               # partition key "run"
            s3_loc  = p["StorageDescriptor"]["Location"]  # s3://.../run=<run_val>/
            parts.append((run_val, s3_loc))
        token = res.get("NextToken")
        if not token: break

    if not parts:
        raise RuntimeError("No partitions found in Glue Catalog table "
                           f"{CATALOG_DB}.{CATALOG_TABLE}")
    # run values are ISO-like strings; lexical max works
    run_val, s3_loc = max(parts, key=lambda x: x[0])
    print("Latest partition:", run_val)
    print("S3 location:     ", s3_loc)
    return run_val, s3_loc

def copy_into_snowflake(s3_loc):
    if not (SF_ACCOUNT and SF_USER and SF_PASSWORD):
        raise RuntimeError("Missing Snowflake env vars (SNOWFLAKE_ACCOUNT, USER, PASSWORD).")
    if not (AWS_READ_KEY and AWS_READ_SECRET):
        raise RuntimeError("Missing AWS read creds (AWS_READ_KEY, AWS_READ_SECRET).")

    conn = snowflake.connector.connect(
        account=SF_ACCOUNT, user=SF_USER, password=SF_PASSWORD,
        role=SF_ROLE, warehouse=SF_WAREHOUSE, database=SF_DATABASE, schema=SF_SCHEMA,
    )
    cs = conn.cursor()
    try:
        cs.execute("CREATE OR REPLACE TABLE STUDENTS_CURATED (STUDENT_ID NUMBER, NAME STRING, AGE NUMBER, CITY STRING)")
        # temp stage pointed to the exact partition we discovered from the Catalog
        stage_sql = f"""
          CREATE OR REPLACE TEMP STAGE STG_STUDENTS_CURATED
          URL='{s3_loc}'
          CREDENTIALS=(AWS_KEY_ID='{AWS_READ_KEY}', AWS_SECRET_KEY='{AWS_READ_SECRET}')
          FILE_FORMAT=(TYPE=PARQUET)
        """
        cs.execute(stage_sql)
        cs.execute("""
          COPY INTO STUDENTS_CURATED
          FROM @STG_STUDENTS_CURATED
          MATCH_BY_COLUMN_NAME=CASE_INSENSITIVE
          FORCE=TRUE
        """)
        cnt = cs.execute("SELECT COUNT(*) FROM STUDENTS_CURATED").fetchone()[0]
        print("Snowflake load complete. Row count:", cnt)
    finally:
        cs.close()
        conn.close()

def main():
    glue = boto3.client("glue", region_name=REGION)

    run_id = datetime.now(UTC).strftime("run=%Y%m%dT%H%M%SZ")
    print("RUN_ID:", run_id)

    # 1) run ETL
    job_run_id = start_glue_job(glue, run_id)
    print("Started job:", JOB_NAME, "JobRunId:", job_run_id)
    state = wait_glue_job(glue, job_run_id)
    if state != "SUCCEEDED":
        raise RuntimeError(f"Glue job failed with state: {state}")
    print("Glue ETL succeeded.")

    # 2) update Catalog
    status = start_and_wait_crawler(glue)
    if status != "SUCCEEDED":
        raise RuntimeError(f"Crawler finished with status: {status}")
    print("Catalog updated.")

    # 3) discover latest partition from Catalog, then COPY to Snowflake
    _, s3_loc = latest_partition_location(glue)
    copy_into_snowflake(s3_loc)

if __name__ == "__main__":
    main()
