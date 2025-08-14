/*
# FILE: glue.tf
resource "aws_glue_catalog_database" "db" {
  name = "${var.project_name}_db"
}

# Minimal Glue Job that points at the uploaded script.
resource "aws_glue_job" "etl" {
  count      = 0  # disable creation for now; we’ll enable later
  name       = "${var.project_name}-etl"
  role_arn   = "arn:aws:iam::${var.account_id}:role/${var.project_name}-glue-role"

  glue_version       = "4.0"
  number_of_workers  = 2
  worker_type        = "G.1X"
  timeout            = 30

    command {
    name            = "glueetl"
    script_location = "s3://myproject-etl-scripts/glue_job.py"
    python_version  = "3"
  }

  default_arguments = {
    "--job-language"                     = "python"
    "--enable-continuous-cloudwatch-log" = "true"
    "--enable-metrics"                   = "true"
    "--TempDir"                          = "s3://${aws_s3_bucket.raw.bucket}/_glue_temp/"
    # Add connectors/libraries here if needed, e.g. Snowflake Spark connector
    # "--additional-python-modules"         = "snowflake-connector-python==3.7.1"
  }

  glue_version = "4.0"
  max_retries  = 1
  timeout      = 30
}

*/