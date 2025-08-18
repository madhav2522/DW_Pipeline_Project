# FILE: terraform/locals.tf
locals {
  glue_db_name  = coalesce(var.glue_db_name,  "${var.project_name}_db")
  glue_job_name = coalesce(var.glue_job_name, "${var.project_name}-etl")
}