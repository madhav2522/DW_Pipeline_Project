#############################################
# Glue: Catalog DB, Crawlers, ETL Job
#############################################

# Database used by crawlers and (optionally) the job
resource "aws_glue_catalog_database" "db" {
  name = local.glue_db_name
  tags = var.tags
}

# ---------- RAW CRAWLER (first run / schema change) ----------
resource "aws_glue_crawler" "raw" {
  count         = var.enable_raw_crawler ? 1 : 0
  name          = var.raw_crawler_name
  role          = aws_iam_role.glue_role.arn
  database_name = aws_glue_catalog_database.db.name
  table_prefix  = var.raw_table_prefix

  s3_target {
    path = "s3://${aws_s3_bucket.raw.bucket}/${var.raw_prefix}"
  }

  schema_change_policy {
    update_behavior = "UPDATE_IN_DATABASE"
    delete_behavior = "LOG"
  }

  recrawl_policy {
    recrawl_behavior = "CRAWL_EVERYTHING"
  }

  tags = var.tags
}

# ---------- CURATED CRAWLER (runs after ETL) ----------
resource "aws_glue_crawler" "curated" {
  count         = var.enable_curated_crawler ? 1 : 0
  name          = var.curated_crawler_name
  role          = aws_iam_role.glue_role.arn
  database_name = aws_glue_catalog_database.db.name
  table_prefix  = var.curated_table_prefix

  # Crawl curated parquet under students_transformed/
  s3_target {
    path = "s3://${aws_s3_bucket.raw.bucket}/${var.curated_prefix}/${var.curated_table}/"
  }

  schema_change_policy {
    update_behavior = "UPDATE_IN_DATABASE"
    delete_behavior = "LOG"
  }

  recrawl_policy {
    recrawl_behavior = "CRAWL_EVERYTHING"
  }

  tags = var.tags
}

# ---------- GLUE ETL JOB ----------
# Script is uploaded separately via aws_s3_object.glue_job_script (see s3.tf)
resource "aws_glue_job" "etl" {
  count      = var.enable_glue_job ? 1 : 0
  name       = local.glue_job_name
  role_arn   = aws_iam_role.glue_role.arn

  glue_version      = var.glue_version
  number_of_workers = var.glue_num_workers
  worker_type       = var.glue_worker_type
  max_retries       = var.glue_max_retries
  timeout           = var.glue_timeout_minutes

  command {
    name            = "glueetl"
    python_version  = "3"
    script_location = "s3://${aws_s3_bucket.scripts.bucket}/${aws_s3_object.glue_job_script.key}"
  }

  # Safe defaults; your Python launcher can override args when it calls start_job_run
  default_arguments = {
    "--job-language"                      = "python"
    "--enable-continuous-cloudwatch-log"  = "true"
    "--enable-metrics"                    = "true"
    "--TempDir"                           = "s3://${aws_s3_bucket.raw.bucket}/_glue_temp/"
    # Optionally provide fallbacks (overridden at runtime by your script):
    "--RAW_BUCKET"                        = aws_s3_bucket.raw.bucket
    "--CURATED_PREFIX"                    = var.curated_prefix
  }

  # Ensure the script is uploaded before the job is created
  depends_on = [aws_s3_object.glue_job_script]

  tags = var.tags
}
