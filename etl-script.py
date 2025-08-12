import sys
from datetime import datetime
import boto3
from awsglue.utils import getResolvedOptions
from awsglue.context import GlueContext
from awsglue.job import Job
from pyspark.context import SparkContext
from pyspark.sql import functions as F

# --------- read args (required) ---------
args = getResolvedOptions(sys.argv, ["JOB_NAME", "BUCKET"])
BUCKET = args["BUCKET"]
LOAD_DATE = datetime.utcnow().strftime("%Y%m%d")

# --------- contexts ---------
sc = SparkContext()
glue_ctx = GlueContext(sc)
spark = glue_ctx.spark_session
job = Job(glue_ctx)
job.init(args["JOB_NAME"], args)

# --------- Initialize boto3 Glue client and trigger the Crawler ---------
glue_client = boto3.client('glue', region_name='us-east-2')  # Replace with your region
crawler_name = 'dw-pipeline-crawler'  # Name of your Glue Crawler

# Start the Glue Crawler to update the catalog with any new or changed data
try:
    response = glue_client.start_crawler(Name=crawler_name)
    print(f"Crawler {crawler_name} started successfully!")
except Exception as e:
    print(f"Error starting the crawler: {e}")
    exit(1)

# --------- source tables in Glue Catalog ---------
DB = "dw_pipeline_db"
STUDENTS_TBL = "students_csv"  # Changed to match your newly created table
EXAMS_TBL = "exams_csv"        # Changed to match your newly created table

# Read as DynamicFrames then to DataFrames
students_df = glue_ctx.create_dynamic_frame.from_catalog(
    database=DB, table_name=STUDENTS_TBL
).toDF()

exams_df = glue_ctx.create_dynamic_frame.from_catalog(
    database=DB, table_name=EXAMS_TBL
).toDF()

# --------- DEBUG: Print Columns ---------
# Print available columns to check if 'student_id' and other required columns exist
print("Columns in students DataFrame:", students_df.columns)
print("Columns in exams DataFrame:", exams_df.columns)

# --------- normalize / cast types ---------
students_df = (
    students_df
    .withColumn("student_id", F.col("student_id").cast("int"))
    .withColumn("name", F.col("name").cast("string"))
    .withColumn("age", F.col("age").cast("int"))
    .withColumn("city", F.col("city").cast("string"))
)

exams_df = (
    exams_df
    .withColumn("student_id", F.col("student_id").cast("int"))
    .withColumn("subject", F.col("subject").cast("string"))
    .withColumn("score", F.col("score").cast("double"))
    .withColumn("exam_date", F.to_date("exam_date"))
)

# --------- transform: average score per student ---------
perf_df = (
    exams_df
    .groupBy("student_id")
    .agg(F.avg("score").alias("avg_score"))
)

# Join with student info
result_df = (
    students_df.alias("s")
    .join(perf_df.alias("p"), on="student_id", how="left")
    .select(
        F.col("student_id"),
        F.col("name"),
        F.col("age"),
        F.col("city"),
        F.round(F.col("avg_score"), 2).alias("avg_score")
    )
    .orderBy("student_id")
)

# --------- write curated parquet to S3 (partitioned by load_date) ---------
out_prefix = f"s3://{BUCKET}/curated/student_performance/load_date={LOAD_DATE}/"
(
    result_df
    .coalesce(1)  # Optional: reduce to 1 file
    .write.mode("overwrite")
    .option("compression", "snappy")
    .parquet(out_prefix)
)

print(f"Wrote curated parquet to: {out_prefix}")
job.commit()
