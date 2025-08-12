# FILE: providers.tf
provider "aws" {
  region = var.aws_region
}

# Tip: you can omit user/password here and set SNOWFLAKE_* env vars instead.
provider "snowflake" {
  account  = var.snowflake_account
  user     = var.snowflake_user
  password = var.snowflake_password
  role     = var.snowflake_role
}
