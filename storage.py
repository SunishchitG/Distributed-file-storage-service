import boto3
from uuid import uuid4
import os

# Configure local Minio or AWS S3 appropriately
S3_BUCKET = "files"
S3_ENDPOINT = os.environ.get("S3_ENDPOINT", "http://localhost:9000")
S3_ACCESS_KEY = os.environ.get("S3_KEY", "minioadmin")
S3_SECRET_KEY = os.environ.get("S3_SECRET", "minioadmin")

s3 = boto3.client('s3',
    endpoint_url=S3_ENDPOINT,
    aws_access_key_id=S3_ACCESS_KEY,
    aws_secret_access_key=S3_SECRET_KEY,
)

def upload_file_obj(file_obj, file_path):
    s3.upload_fileobj(file_obj, S3_BUCKET, file_path)

def download_file_obj(file_path):
    out = s3.get_object(Bucket=S3_BUCKET, Key=file_path)
    return out["Body"].read()
