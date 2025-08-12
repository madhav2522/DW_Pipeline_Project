# FILE: variables.tf
variable "aws_region" {
  type    = string
  default = "us-east-2"
}

variable "account_id" {
  description = "AWS Account ID"
  type        = string
}

variable "region" {
  description = "AWS region"
  type        = string
}

variable "project_name" {
  type    = string
  default = "myproject"
}

variable "s3_bucket_raw" {
  type    = string
  default = "myproject-raw-data"
}

variable "s3_bucket_scripts" {
  type    = string
  default = "myproject-etl-scripts"
}

variable "snowflake_account" {
  description = "Snowflake account locator (e.g., abcd-xy12345)"
  type        = string
}

variable "snowflake_user" {
  type = string
}

variable "snowflake_password" {
  type      = string
  sensitive = true
}

variable "snowflake_role" {
  type    = string
  default = "SYSADMIN"
}

variable "snowflake_warehouse" {
  type    = string
  default = "COMPUTE_WH"
}

variable "snowflake_database" {
  type    = string
  default = "MY_DB"
}

variable "snowflake_schema" {
  type    = string
  default = "PUBLIC"
}
