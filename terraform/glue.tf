# FILE: glue.tf
resource "aws_glue_catalog_database" "db" {
  name = "${var.project_name}_db"
}

# Minimal Glue Job that points at the uploaded script.
resource "aws_glue_job" "etl" {
  name     = "${var.project_name}-glue-etl"
  role_arn = aws_iam_role.glue_role.arn

  command {
    name            = "glueetl"
    python_version  = "3"
    script_location = "s3://${aws_s3_bucket.scripts.bucket}/${aws_s3_object.glue_job_script.key}"
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
