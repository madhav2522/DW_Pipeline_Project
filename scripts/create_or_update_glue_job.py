#!/usr/bin/env python3
import boto3, botocore, os

JOB_NAME    = "myproject-etl"
ROLE_NAME   = "myproject-glue-role"
SCRIPT_LOC  = "s3://myproject-etl-scripts/etl_scripts/glue_job.py"  # students-only ETL
GLUE_VER    = "4.0"
WORKER_TYPE = "G.1X"
NUM_WORKERS = 4
TIMEOUT     = 45  # minutes

REGION = os.getenv("AWS_REGION", "us-east-2")
iam  = boto3.client("iam",  region_name=REGION)
glue = boto3.client("glue", region_name=REGION)

def role_arn(name: str) -> str:
    return iam.get_role(RoleName=name)["Role"]["Arn"]

def main():
    arn = role_arn(ROLE_NAME)
    default_args = {
        "--job-language": "python",
        "--enable-continuous-cloudwatch-log": "true",
        "--enable-metrics": "true",
        "--TempDir": f"s3://myproject-etl-scripts/tmp/{JOB_NAME}/"
    }
    try:
        glue.get_job(JobName=JOB_NAME)
        glue.update_job(
            JobName=JOB_NAME,
            JobUpdate={
                "Role": arn,
                "Command": {"Name": "glueetl", "ScriptLocation": SCRIPT_LOC, "PythonVersion": "3"},
                "GlueVersion": GLUE_VER,
                "WorkerType": WORKER_TYPE,
                "NumberOfWorkers": NUM_WORKERS,
                "Timeout": TIMEOUT,
                "DefaultArguments": default_args
            }
        )
        print(f"✅ Updated Glue job {JOB_NAME}")
    except botocore.exceptions.ClientError as e:
        if e.response["Error"]["Code"] == "EntityNotFoundException":
            glue.create_job(
                Name=JOB_NAME,
                Role=arn,
                Command={"Name": "glueetl", "ScriptLocation": SCRIPT_LOC, "PythonVersion": "3"},
                GlueVersion=GLUE_VER,
                WorkerType=WORKER_TYPE,
                NumberOfWorkers=NUM_WORKERS,
                Timeout=TIMEOUT,
                DefaultArguments=default_args
            )
            print(f"✅ Created Glue job {JOB_NAME}")
        else:
            raise

if __name__ == "__main__":
    main()
