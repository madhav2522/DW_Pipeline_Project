#############################################
# Raw uploader (human/script) - minimal auth
#############################################

data "aws_iam_policy_document" "glue_assume" {
  statement {
    effect = "Allow"
    principals {
      type        = "Service"
      identifiers = ["glue.amazonaws.com"]
    }
    actions = ["sts:AssumeRole"]
  }
}

# 1) IAM user for the upload
resource "aws_iam_user" "raw_uploader" {
  name = "${var.project_name}-raw-uploader"
}

# 2) Policy: list only students/ prefix; put only this exact object
resource "aws_iam_policy" "allow_put_students_large" {
  name        = "${var.project_name}-put-students-large"
  description = "Allow List on students/ and PutObject for students_large.csv"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid      = "ListBucketPrefix"
        Effect   = "Allow"
        Action   = ["s3:ListBucket"]
        Resource = "arn:aws:s3:::myproject-raw-data-103259692325-us-east-2"
        Condition = {
          StringLike = { "s3:prefix" = ["students/*"] }
        }
      },
      {
        Sid      = "PutSpecificObject"
        Effect   = "Allow"
        Action   = ["s3:PutObject", "s3:AbortMultipartUpload"]
        Resource = "arn:aws:s3:::myproject-raw-data-103259692325-us-east-2/students/students_large.csv"
      }
    ]
  })
}

# 3) Attach the policy to the user
resource "aws_iam_user_policy_attachment" "attach_put_students_large" {
  user       = aws_iam_user.raw_uploader.name
  policy_arn = aws_iam_policy.allow_put_students_large.arn
}

# 4) Create an access key for this user (Terraform will output it)
resource "aws_iam_access_key" "raw_uploader_key" {
  user = aws_iam_user.raw_uploader.name
}

resource "aws_iam_role" "glue_role" {
  name               = "${var.project_name}-glue-role"
  assume_role_policy = data.aws_iam_policy_document.glue_assume.json
}
