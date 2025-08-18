# scripts/run_crawler.py

"""
export AWS_REGION=us-east-2
# and your creds via env or ~/.aws/credentials / AWS_PROFILE

python scripts/run_crawler.py

"""

import os, time, sys
import boto3
from botocore.exceptions import ClientError

REGION = os.getenv("AWS_REGION", "us-east-2")
CRAWLER_NAME = os.getenv("GLUE_RAW_CRAWLER_NAME", "dw-pipeline-crawler")  # set your raw crawler name

glue = boto3.client("glue", region_name=REGION)

def start_and_wait_crawler(name: str):
    try:
        glue.start_crawler(Name=name)
        print(f"Crawler {name} started.")
    except glue.exceptions.CrawlerRunningException:
        print(f"Crawler {name} is already running; waiting for it to finish...")
    except ClientError as e:
        print(f"ERROR starting crawler {name}: {e}")
        sys.exit(1)

    # Poll status until READY
    while True:
        c = glue.get_crawler(Name=name)["Crawler"]
        state = c.get("State")
        last = c.get("LastCrawl", {}).get("Status")
        print(f"State: {state}  LastStatus: {last}")
        if state == "READY":
            print(f"Crawler {name} finished with status: {last}")
            break
        time.sleep(8)

if __name__ == "__main__":
    start_and_wait_crawler(CRAWLER_NAME)
