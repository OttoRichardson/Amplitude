import os
import sys
from dotenv import load_dotenv
import boto3


load_dotenv()

aws_access_key = os.getenv('AWS_ACCESS_KEY')
AWS_ACCESS_SECRET_KEY = os.getenv('AWS_ACCESS_SECRET_KEY')
bucket = os.getenv('AWS_BUCKET_NAME')

s3_client = boto3.client(
    's3',
    aws_access_key_id=aws_access_key,
    aws_secret_access_key=AWS_ACCESS_SECRET_KEY
)


output_folder = "data"

files_to_upload = []
for root, _, filenames in os.walk(output_folder):
    files_to_upload.extend(filenames)


#print(files_to_upload)

for file in files_to_upload:
    aws_file_destination = "python-import/" + file
    output_path = output_folder + "/" + file
    s3_client.upload_file(output_path, bucket, aws_file_destination)
    print(f"Uploaded: {file}")
    
    try:
        os.remove(output_path)
        print(f"Deleted local file: {output_path}")
    except OSError as e:
        print(f"Error deleting {output_path}: {e}")

