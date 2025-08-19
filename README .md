# DW_Pipeline_Project — S3(RAW) → Glue ETL → Parquet → Glue Catalog → S3(CURATED)→ Snowflake 

## 📑 Table of Contents
1. [Overview](#-overview)
2. [Problem Statement](#-problem-statement)
3. [Tech Stack](#-tech-stack)
4. [Architecture](#-architecture)
5. [Repository Structure](#-repository-structure)
6. [Prerequisites](#-prerequisites)
7. [Provision Infrastructure](#-provision-infrastructure-with-terraform)
8. [Running the Pipeline](#-running-the-pipeline-end-to-end)
9. [ETL Transformations](#-etl-transformations-typical)
10. [Glue Catalog Behavior](#-glue-catalog-behavior)
11. [Validation in Snowflake](#-validation-in-snowflake)
12. [Acceptance Criteria](#-acceptance-criteria-assignment-4)
13. [Troubleshooting](#-troubleshooting)
14. [Security & Git Hygiene](#-security--git-hygiene)
15. [License](#-license)

---

## 📌 Overview
This project implements a **batch data warehouse pipeline** that ingests **student-related CSV datasets** (*Students*, *Exams*) into **Amazon S3**, transforms them with **AWS Glue** (Apache Spark), catalogs curated Parquet data with **Glue Data Catalog**, and loads the latest partitions into **Snowflake** for analytics.

The entire solution is automated with **Terraform** and **AWS SDK (boto3)** — no AWS Management Console involvement.

---

## 🎯 Problem Statement
Education analytics requires integrating multiple CSV exports (e.g., students roster, exam results) into a consistent, query-ready warehouse.  
Manual processes are:
- Error-prone
- Slow to deploy
- Hard to maintain

This project solves the problem by:
- Automating resource provisioning with Terraform
- Using Glue ETL for scalable transformations
- Loading curated partitions into Snowflake
- Dynamically discovering the newest partition via Glue Catalog

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
    A[Students & Exams CSV Data] -->|Python Ingestion| B[S3 Raw Bucket]
    B -->|Glue Crawler| C[Glue Data Catalog]
    C -->|Glue ETL (PySpark)| D[S3 Curated Bucket (Parquet)]
    D -->|Snowflake COPY INTO| E[Snowflake Tables: STUDENTS_CURATED, EXAMS_CURATED]
    E --> F[Analytics & BI Tools]
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
├── scripts/ # Python orchestration scripts
│ ├── data_generation.py # Generates synthetic student/exam data
│ ├── upload_large_to_s3.py # Uploads Students datasets to S3
│ ├── run_crawler.py # Starts the Glue crawler
│ └── run_students_glue_job.py # Runs the Glue ETL job
│
├── terraform/ # Infrastructure as Code (IaC)
│ ├── glue.tf # Glue jobs & crawlers
│ ├── iam.tf # IAM roles & policies
│ ├── locals.tf # Local variables
│ ├── outputs.tf # Terraform outputs
│ ├── providers.tf # AWS & Snowflake providers
│ ├── s3.tf # S3 buckets
│ ├── secrets.auto.tfvars # Secrets (Snowflake credentials, etc.)
│ ├── snowflake.tf # Snowflake warehouse, DB, schema, tables
│ ├── variables.tf # Input variables
│ ├── versions.tf # Provider versions
│ ├── terraform.tfstate # Terraform state file
│ ├── terraform.tfstate.backup # Backup state file
│ └── .terraform.lock.hcl # Dependency lock file
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
pip install -r requirements.txt
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

Terraform will create:
- S3 buckets (raw, ETL scripts, curated)
- IAM roles & policies for Glue
- Glue Job pointing to `etl_scripts/glue_job.py`
- Glue Catalog database & crawler
- Snowflake warehouse, database, schema, and tables

---

## 🚀 Running the Pipeline (End-to-End)

### 1. Upload Raw CSVs to S3
```bash
python3 scripts/upload_large_to_s3.py
```

### 2. Ensure Glue Script Exists in S3
```bash
python3 scripts/upload_etl_script_to_s3.py
```

### 3. Run ETL → Crawl → Load into Snowflake
```bash
python3 scripts/run_students_glue_job.py
```

This will:
- Start the Glue ETL job with a unique `RUN_ID`
- Run the Glue crawler to register new curated partitions
- Discover the newest partitions in Glue Catalog
- COPY curated data into Snowflake tables

---

## 🔄 ETL Transformations (Typical)

**Students:**
- Normalize column names → `snake_case`
- Trim string values
- Cast `student_id` → BIGINT, `age` → INT
- Drop rows with NULL `student_id`
- Remove duplicates on `student_id`
- Write Parquet → `s3://<bucket>/curated/students_transformed/run=<timestamp>/`

**Exams:**
- Normalize column names → `snake_case`
- Trim string values
- Cast `exam_id` → BIGINT, `student_id` → BIGINT, `score` → INT
- Drop rows with NULL `exam_id` or `student_id`
- De-duplicate on (`exam_id`, `student_id`)
- Write Parquet → `s3://<bucket>/curated/exams_transformed/run=<timestamp>/`

---

## 📒 Glue Catalog Behavior
- Crawlers target curated paths (students + exams)
- Each ETL run adds a partition (`run=YYYYMMDDThhmmssZ`)
- Loader script dynamically finds the newest partitions (no hard-coded S3 paths)

---

## 🔍 Validation in Snowflake
```sql
USE WAREHOUSE COMPUTE_WH;
USE DATABASE MY_DB;
USE SCHEMA PUBLIC;

-- Students
SELECT COUNT(*) AS rows, COUNT(DISTINCT student_id) AS distinct_students
FROM STUDENTS_CURATED;

SELECT * FROM STUDENTS_CURATED ORDER BY student_id LIMIT 20;

-- Exams
SELECT COUNT(*) AS rows, COUNT(DISTINCT exam_id) AS distinct_exams
FROM EXAMS_CURATED;

SELECT * FROM EXAMS_CURATED ORDER BY exam_id LIMIT 20;


```

---

## ✅ Acceptance Criteria (Assignment 4)
- All resources provisioned with Terraform & AWS SDK (no console usage)  
- Raw CSVs land in S3 (`raw/` prefixes)  
- Glue Catalog databases & crawlers discover curated Parquet partitions  
- Glue ETL transforms Students & Exams into curated Parquet  
- Snowflake contains integrated tables (`STUDENTS_CURATED`, `EXAMS_CURATED`) ready for analysis  
- Validation SQL confirms correctness  
- Repo includes code, IaC, and documentation  
- Presentation explains architecture, steps, and code implementation  

---

## 🛠 Troubleshooting

**1. Glue Job fails with module errors**  
→ Ensure `--additional-python-modules` includes `snowflake-connector-python`, and `requests`.

**2. COPY INTO Snowflake fails with permissions**  
→ Verify Snowflake `STORAGE INTEGRATION` role has correct IAM trust + S3 read-only permissions.

**3. Data not visible in Snowflake after ETL run**  
→ Check Glue Crawler ran successfully and new partitions are visible in Glue Catalog.

**4. Terraform errors with state**  
→ Run `terraform init -reconfigure` to refresh providers, or clear `.terraform/` cache.

---

## 🔐 Security & Git Hygiene
- Never commit secrets, Terraform state files, or AWS credentials
- `.gitignore` includes sensitive files
- Rotate any test keys/passwords immediately after use

---

## 📜 License
MIT License — feel free to use and adapt with attribution
