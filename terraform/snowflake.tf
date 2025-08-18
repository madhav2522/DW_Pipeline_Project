# FILE: snowflake.tf
# Warehouse (ensure it exists or let TF create below)
resource "snowflake_warehouse" "wh" {
  name                         = "COMPUTE_WH"
  statement_timeout_in_seconds = 300
  auto_suspend                 = 300
  auto_resume                  = true
  initially_suspended          = true
}

resource "snowflake_database" "db" {
  name = var.snowflake_database
}

resource "snowflake_schema" "schema" {
  name     = var.snowflake_schema
  database = snowflake_database.db.name
}

# Students table
resource "snowflake_table" "students" {
  database = snowflake_database.db.name
  schema   = snowflake_schema.schema.name
  name     = "STUDENTS"

  column {
    name = "STUDENT_ID"
    type = "NUMBER"
  }
  column {
    name = "STUDENT_NAME"
    type = "STRING"
  }
  column {
    name = "EMAIL"
    type = "STRING"
  }
  column {
    name = "ENROLLED_AT"
    type = "TIMESTAMP_NTZ"
  }
}

# Exams table
resource "snowflake_table" "exams" {
  database = snowflake_database.db.name
  schema   = snowflake_schema.schema.name
  name     = "EXAMS"

  column {
    name = "EXAM_ID"
    type = "NUMBER"
  }
  column {
    name = "STUDENT_ID"
    type = "NUMBER"
  }
  column {
    name = "SUBJECT"
    type = "STRING"
  }
  column {
    name = "SCORE"
    type = "NUMBER"
  }
  column {
    name = "TAKEN_AT"
    type = "TIMESTAMP_NTZ"
  }
}
