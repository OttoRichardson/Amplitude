# Single JSON file upload to S3 with KMS key

# Load libraries
import boto3
import os
from dotenv import load_dotenv

# Load .env file
load_dotenv()

# Read .env file
aws_access_key=os.getenv('AWS_ACCESS_KEY')
aws_secret_key=os.getenv('AWS_ACCESS_SECRET_KEY')
aws_bucket_name=os.getenv('AWS_BUCKET_NAME')

# Create S3 Client using AWS Credentials
s3_client = boto3.client(
    's3',
    aws_access_key_id=aws_access_key,
    aws_secret_access_key=aws_secret_key
)

# Set file start and end points
local_file_location = "test_data.json"
aws_file_destination = "python-import/test_data.json"

# Upload file to S3 Bucket
s3_client.upload_file(local_file_location, aws_bucket_name, aws_file_destination)

print("File uploaded")