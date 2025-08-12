import re
import sys
from awsglue.utils import getResolvedOptions
from pyspark.context import SparkContext
from awsglue.context import GlueContext
from awsglue.job import Job

# -------- Defaults that match your Terraform outputs --------
RAW_BUCKET = "myproject-raw-data-103259692325-us-east-2"

DEFAULT_STUDENTS_PATH = f"s3://{RAW_BUCKET}/students/students.csv"
DEFAULT_EXAMS_PATH    = f"s3://{RAW_BUCKET}/exams/exams.csv"

DEFAULT_CURATED_STUDENTS = f"s3://{RAW_BUCKET}/curated/students/"
DEFAULT_CURATED_EXAMS    = f"s3://{RAW_BUCKET}/curated/exams/"
DEFAULT_CURATED_JOINED   = f"s3://{RAW_BUCKET}/curated/joined_students_exams/"

# -------- Parse Glue args (with safe defaults) --------
# Optional runtime overrides (all optional):
# --students_path, --exams_path, --curated_students, --curated_exams, --curated_joined
optional_args = [
    "students_path",
    "exams_path",
    "curated_students",
    "curated_exams",
    "curated_joined",
]
base_args = ["JOB_NAME"]
provided = set(sys.argv)
opt_keys = base_args + [k for k in optional_args if f"--{k}" in provided]
args = getResolvedOptions(sys.argv, opt_keys)

students_path    = args.get("students_path", DEFAULT_STUDENTS_PATH)
exams_path       = args.get("exams_path", DEFAULT_EXAMS_PATH)
curated_students = args.get("curated_students", DEFAULT_CURATED_STUDENTS)
curated_exams    = args.get("curated_exams", DEFAULT_CURATED_EXAMS)
curated_joined   = args.get("curated_joined", DEFAULT_CURATED_JOINED)

# -------- Glue/Spark bootstrap --------
sc = SparkContext()
glueContext = GlueContext(sc)
spark = glueContext.spark_session
job = Job(glueContext)
job.init(args["JOB_NAME"], args)

def normalize_col(c: str) -> str:
    # Trim, lower-case, replace spaces & non-word chars with underscores, collapse repeats
    c = c.strip().lower()
    c = re.sub(r"[^\w]+", "_", c)
    c = re.sub(r"_+", "_", c).strip("_")
    return c

def clean_df(df):
    # Drop fully empty rows, normalize column names, drop exact duplicates
    df2 = df.dropna(how="all")
    for c in df2.columns:
        newc = normalize_col(c)
        if newc != c:
            df2 = df2.withColumnRenamed(c, newc)
    return df2.dropDuplicates()

# -------- Read RAW CSVs --------
students_df = (
    spark.read
         .option("header", "true")
         .option("inferSchema", "true")
         .csv(students_path)
)
exams_df = (
    spark.read
         .option("header", "true")
         .option("inferSchema", "true")
         .csv(exams_path)
)

# -------- Clean --------
students_clean = clean_df(students_df)
exams_clean    = clean_df(exams_df)

# -------- Write curated (separate) --------
(students_clean.coalesce(1)
               .write.mode("overwrite")
               .parquet(curated_students))

(exams_clean.coalesce(1)
            .write.mode("overwrite")
            .parquet(curated_exams))

print(f"[INFO] Wrote curated students to: {curated_students}")
print(f"[INFO] Wrote curated exams to   : {curated_exams}")

# -------- Optional join on student_id (if present in both) --------
join_key = "student_id"
if join_key in [c.lower() for c in students_clean.columns] and join_key in [c.lower() for c in exams_clean.columns]:
    # Ensure the column names match exactly (after normalization they should)
    # Left join: keep all students; bring matching exams columns with suffixes where needed
    # To avoid duplicate column names after join, add prefix to exams columns (except the key).
    exams_prefixed = exams_clean
    for c in exams_clean.columns:
        if c != join_key and c in students_clean.columns:
            exams_prefixed = exams_prefixed.withColumnRenamed(c, f"exams_{c}")

    joined = students_clean.join(exams_prefixed, on=join_key, how="left")

    (joined.coalesce(1)
           .write.mode("overwrite")
           .parquet(curated_joined))
    print(f"[INFO] Wrote curated joined dataset to: {curated_joined}")
else:
    print(f"[INFO] Skipping join: '{join_key}' not found in both datasets. "
          f"students cols: {students_clean.columns} | exams cols: {exams_clean.columns}")

job.commit()
