# FILE: s3.tf
resource "aws_s3_bucket" "raw" {
  bucket = "myproject-raw-data-${var.account_id}-${var.region}"
}

resource "aws_s3_bucket" "scripts" {
  bucket = var.s3_bucket_scripts
}

# Optional: versioning recommended
resource "aws_s3_bucket_versioning" "scripts" {
  bucket = aws_s3_bucket.scripts.id
  versioning_configuration {
    status = "Enabled"
  }
}

# Upload the local Glue script so the job can reference it.
# Make sure the file exists locally at etl_scripts/glue_job.py before 'apply'.
resource "aws_s3_object" "glue_job_script" {
  bucket = aws_s3_bucket.scripts.id
  key    = "etl_scripts/glue_job.py"
  etag   = filemd5("../etl_scripts/glue_job.py")
  source = "../etl_scripts/glue_job.py"

}
