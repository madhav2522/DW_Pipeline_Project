# FILE: variables.tf

#############################################
# Core AWS / Project settings
#############################################

variable "aws_region" {
  type        = string
  description = "Primary AWS region to deploy resources into."
  default     = "us-east-2"
}

variable "account_id" {
  type        = string
  description = "AWS Account ID"
}

variable "region" {
  type        = string
  description = "AWS region (kept for compatibility if referenced elsewhere)."
}

variable "project_name" {
  type        = string
  description = "Project name used as a prefix for resource names."
  default     = "myproject"
}

#############################################
# S3 buckets
#############################################

variable "s3_bucket_raw" {
  type        = string
  description = "Raw data bucket name (curated lives under a prefix in this bucket)."
  default     = "myproject-raw-data"
}

variable "s3_bucket_scripts" {
  type        = string
  description = "Bucket where ETL scripts (Glue job script) are stored."
  default     = "myproject-etl-scripts"
}

#############################################
# Snowflake config
#############################################

variable "snowflake_account" {
  type        = string
  description = "Snowflake account locator (e.g., abcd-xy12345)"
}

variable "snowflake_user" {
  type        = string
  description = "Snowflake username."
}

variable "snowflake_password" {
  type        = string
  sensitive   = true
  description = "Snowflake password (sensitive)."
}

variable "snowflake_role" {
  type        = string
  description = "Default Snowflake role to use."
  default     = "SYSADMIN"
}

variable "snowflake_warehouse" {
  type        = string
  description = "Snowflake warehouse name."
  default     = "COMPUTE_WH"
}

variable "snowflake_database" {
  type        = string
  description = "Snowflake database name."
  default     = "MY_DB"
}

variable "snowflake_schema" {
  type        = string
  description = "Snowflake schema name."
  default     = "PUBLIC"
}

#############################################
# Feature flags
#############################################

variable "enable_glue_job" {
  type        = bool
  description = "Create/manage the Glue ETL job."
  default     = false
}

variable "enable_raw_crawler" {
  type        = bool
  description = "Create/manage the RAW crawler."
  default     = false
}

variable "enable_curated_crawler" {
  type        = bool
  description = "Create/manage the CURATED crawler."
  default     = false
}

#############################################
# Glue Naming / Database / Crawlers
#############################################

variable "glue_db_name" {
  type        = string
  description = "Glue Catalog database name."
  default     = null
}

variable "glue_job_name" {
  type        = string
  description = "Glue ETL job name."
  default     = null
}

variable "raw_crawler_name" {
  type        = string
  description = "Name for the RAW crawler."
  default     = "dw-pipeline-crawler"
}

variable "curated_crawler_name" {
  type        = string
  description = "Name for the CURATED crawler."
  default     = "students_curated_crawler"
}

#############################################
# S3 prefixes / table directories
#############################################

variable "raw_prefix" {
  type        = string
  description = "RAW data prefix under the raw bucket."
  default     = "students/"
}

variable "curated_prefix" {
  type        = string
  description = "Top-level curated prefix under the raw bucket."
  default     = "curated"
}

variable "curated_table" {
  type        = string
  description = "Curated table directory under curated prefix (used by crawler)."
  default     = "students_transformed"
}

variable "raw_table_prefix" {
  type        = string
  description = "Optional RAW table name prefix that the crawler prepends."
  default     = ""
}

variable "curated_table_prefix" {
  type        = string
  description = "Optional CURATED table name prefix that the crawler prepends."
  default     = ""
}

#############################################
# Glue Job sizing / runtime
#############################################

variable "glue_version" {
  type        = string
  description = "Glue version for the job runtime."
  default     = "4.0"
}

variable "glue_worker_type" {
  type        = string
  description = "Glue worker type (e.g., G.1X, G.2X)."
  default     = "G.1X"
}

variable "glue_num_workers" {
  type        = number
  description = "Number of Glue workers."
  default     = 2
}

variable "glue_max_retries" {
  type        = number
  description = "Max retries for the Glue job."
  default     = 1
}

variable "glue_timeout_minutes" {
  type        = number
  description = "Glue job timeout in minutes."
  default     = 30
}

#############################################
# Optional tags
#############################################

variable "tags" {
  type        = map(string)
  description = "Tags to apply to supported resources."
  default     = {}
}
