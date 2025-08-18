# DW_Pipeline_Project — S3 → Glue ETL → Parquet → Glue Catalog → Snowflake

## 📌 Overview
This project implements a **batch data warehouse pipeline** that ingests a large CSV dataset into **Amazon S3**, transforms it with **AWS Glue** (Apache Spark), catalogs the curated data with **Glue Data Catalog**, and loads the latest partition into **Snowflake**.

The goal is to create a **fully automated, reproducible ETL workflow** using **Terraform** and **AWS SDK (boto3)** — with **no use of the AWS Management Console**.

---

## 🎯 Problem Statement
Manual data ingestion and transformation pipelines are:
- Error-prone
- Slow to deploy
- Difficult to maintain

This project addresses these issues by:
- Automating AWS and Snowflake resource creation with **Terraform**
- Using **Glue ETL** for scalable, serverless transformations
- Loading curated data into Snowflake for analytics
- Dynamically discovering the latest partition in Glue Catalog to avoid hard-coded S3 paths

---

## 🛠 Tech Stack
- **Infrastructure**: Terraform, AWS CLI
- **AWS Services**: S3, Glue, Glue Catalog, IAM, Secrets Manager
- **Data Warehouse**: Snowflake
- **Languages**: Python (boto3, Snowflake Connector), SQL, PySpark
- **Data Formats**: CSV (input), Parquet (curated)

---

## 📊 Architecture
```mermaid
flowchart TD
    A[Students CSV Data] -->|Python Ingestion| B[S3 Raw Bucket]
    B -->|Glue RAW Crawler| C[Glue Data Catalog]
    C -->|Glue ETL (PySpark)| D[S3 Curated (Parquet)]
    D -->|Snowflake COPY INTO| E[Snowflake STUDENTS_CURATED]
    E --> F[Analytics / BI]
```

---

## 📂 Repository Structure
```
DW_Pipeline_Project/
├── data/
│   ├── Exams.csv
│   ├── students_large.csv
│   └── Students.csv
│
├── etl_scripts/
│   └── glue_job.py
│
├── scripts/
│   ├── data_generation.py
│   ├── run_students_glue_job.py
│   ├── run_crawler.py
│   └── upload_large_to_s3.py
│
├── terraform/
│   ├── glue.tf
│   ├── iam.tf
│   ├── outputs.tf
│   ├── providers.tf
│   ├── s3.tf
│   ├── snowflake.tf
│   ├── variables.tf
│   ├── versions.tf
│   ├── terraform.tfstate
│   ├── terraform.tfstate.backup
│   ├── terraform.lock.hcl
│   └── .terraform/ (Terraform cache directory)
│
├── .gitignore
└── README.md
```

---

## ⚙️ Prerequisites

### 1. Python & Virtual Environment
```bash
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install boto3 "snowflake-connector-python>=3.10,<4.0"
```

### 2. AWS Environment Variables
```bash
export AWS_REGION=us-east-2
```

### 3. Snowflake Environment Variables
```bash
export SNOWFLAKE_ACCOUNT=<ACCOUNT_ID>
export SNOWFLAKE_USER=<USERNAME>
export SNOWFLAKE_PASSWORD=<PASSWORD>
export SNOWFLAKE_ROLE=ACCOUNTADMIN
export SNOWFLAKE_WAREHOUSE=COMPUTE_WH
export SNOWFLAKE_DATABASE=MY_DB
export SNOWFLAKE_SCHEMA=PUBLIC
```

### 4. AWS Read-Only Keys for Snowflake
(Snowflake will use these to read curated data from S3.)
```bash
export AWS_READ_KEY=<AWS_READ_KEY>
export AWS_READ_SECRET=<AWS_READ_SECRET>
```

---

## 🏗 Provision Infrastructure with Terraform
```bash
cd terraform
terraform init
terraform validate
terraform plan
terraform apply
cd ..
```

**Terraform will create:**
- **S3** buckets (raw, ETL scripts, curated)
- **IAM** roles and policies for Glue
- **Glue** Job pointing to `etl_scripts/glue_job.py`
- **Glue Catalog** database and crawler
- **Snowflake** warehouse, database, schema, and table

---

## 🚀 Running the Pipeline (End-to-End)

### 1. Upload Raw CSV to S3
```bash
python3 scripts/upload_large_to_s3.py
```

### 2. Ensure Glue Script Exists in S3
(Only if Terraform did not upload it already.)
```bash
python3 scripts/upload_etl_script_to_s3.py
```

### 3. Run ETL → Crawl → Load into Snowflake
```bash
python3 scripts/run_students_glue_job.py
```

This will:
- Start the Glue ETL job with a unique `RUN_ID` (e.g., `run=20250813T221849Z`)
- Start the Glue crawler to register the new partition
- Discover the latest partition in Glue Catalog
- Run `COPY INTO` in Snowflake to load the new data

---

## 🔍 Validation in Snowflake
```sql
USE WAREHOUSE COMPUTE_WH;
USE DATABASE MY_DB;
USE SCHEMA PUBLIC;

SELECT COUNT(*) AS rows, COUNT(DISTINCT student_id) AS distinct_ids
FROM STUDENTS_CURATED;

SELECT * FROM STUDENTS_CURATED ORDER BY student_id LIMIT 20;
```

---

## 🔄 ETL Transformations
- Normalize column names → `snake_case`
- Trim all string values
- Cast `student_id` → BIGINT, `age` → INT
- Drop rows with NULL `student_id`
- Remove duplicate `student_id` entries
- Write Parquet output to:
  ```
  s3://<BUCKET>/curated/students_transformed/run=<UTC_TIMESTAMP>/
  ```

---

## 📒 Glue Catalog Behavior
- Crawler targets `.../curated/students_transformed/`
- Each ETL run adds a partition (`run=YYYYMMDDThhmmssZ`)
- Loader script dynamically discovers the newest partition — no hard-coded S3 paths

---

## ✅ Acceptance Criteria
- All AWS resources provisioned with **Terraform** and **AWS SDK** (no console usage)  
- Raw and curated data stored in **S3**  
- **Glue Catalog** & **Glue ETL** configured to transform and load into **Snowflake**  
- Snowflake contains integrated data ready for analysis  
- SQL validation scripts confirm data correctness  
- Repository contains complete code, infra definitions, and documentation  
- Presentation prepared for class demo

---

## 🔐 Security & Git Hygiene
- **Do not commit** secrets, Terraform state files, or run ID files
- `.gitignore` includes these sensitive files
- Rotate any shared keys/passwords after testing

---

## 📜 License
MIT License — feel free to use and adapt with attribution
