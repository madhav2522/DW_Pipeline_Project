# FILE: outputs.tf
output "s3_raw_bucket" {
  value = aws_s3_bucket.raw.bucket
}

output "s3_scripts_bucket" {
  value = aws_s3_bucket.scripts.bucket
}

output "glue_job_name" {
  value = aws_glue_job.etl.name
}

output "snowflake_db" {
  value = snowflake_database.db.name
}

output "snowflake_schema" {
  value = snowflake_schema.schema.name
}

output "snowflake_warehouse" {
  value = snowflake_warehouse.wh.name
}
