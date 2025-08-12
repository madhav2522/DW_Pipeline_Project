import boto3

BUCKET = "myproject-etl-scripts"  # Matches Terraform bucket for scripts
KEY    = "etl_scripts/glue_job.py"  # Must match Glue job's script_location
LOCAL  = "etl_scripts/glue_job.py"  # Correct relative path to your file

boto3.client("s3").upload_file(LOCAL, BUCKET, KEY)
print(f"✅ Uploaded {LOCAL} -> s3://{BUCKET}/{KEY}")
