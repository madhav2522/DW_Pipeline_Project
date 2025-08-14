#!/usr/bin/env python3
# Glue 4.0 (Spark 3.x) — students_only
# Reads:  s3://<RAW_BUCKET>/<STUDENTS_KEY>
# Writes: s3://<RAW_BUCKET>/<CURATED_PREFIX>/students_transformed/run=YYYYMMDDThhmmssZ/

import argparse
from datetime import datetime
from pyspark.sql import SparkSession
from pyspark.sql.functions import col, trim
from pyspark.sql.types import IntegerType, LongType, StringType

# Parse args (tolerant to extra Glue args)
p = argparse.ArgumentParser()
p.add_argument("--RAW_BUCKET", required=True)
p.add_argument("--STUDENTS_KEY", required=True)       # e.g., students/students_large.csv
p.add_argument("--CURATED_PREFIX", default="curated")  # e.g., curated
p.add_argument("--RUN_ID", default=None)
args, _ = p.parse_known_args()

RAW_BUCKET     = args.RAW_BUCKET
STUDENTS_KEY   = args.STUDENTS_KEY
CURATED_PREFIX = args.CURATED_PREFIX
RUN_ID         = args.RUN_ID or datetime.utcnow().strftime("run=%Y%m%dT%H%M%SZ")

spark = SparkSession.builder.appName("students-only-etl").getOrCreate()
spark.conf.set("spark.sql.sources.partitionOverwriteMode", "dynamic")

src  = f"s3://{RAW_BUCKET}/{STUDENTS_KEY}"
dest = f"s3://{RAW_BUCKET}/{CURATED_PREFIX}/students_transformed/{RUN_ID}/"

# Read raw CSV
df = (spark.read.option("header","true")
              .option("inferSchema","true")
              .csv(src))

# Normalize column names -> snake_case-ish
def norm(n: str) -> str: return n.strip().lower().replace(" ", "_")
for c in df.columns:
    df = df.withColumnRenamed(c, norm(c))

# Trim only (no lowercasing of values)
for f in df.schema.fields:
    if isinstance(f.dataType, StringType):
        df = df.withColumn(f.name, trim(col(f.name)))

# Casts for your columns if present
if "student_id" in df.columns:
    df = df.withColumn("student_id", col("student_id").cast(LongType()))
if "age" in df.columns:
    df = df.withColumn("age", col("age").cast(IntegerType()))

# Keep valid rows, simple de-dupe by student_id
if "student_id" in df.columns:
    df = df.filter(col("student_id").isNotNull()).dropDuplicates(["student_id"])

# Write curated parquet
df.repartition(32).write.mode("overwrite").parquet(dest)
print(f"✅ Wrote curated parquet to: {dest}")
spark.stop()
