import os
from dotenv import load_dotenv
import boto3

load_dotenv()

AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID")
AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")
AWS_REGION = os.getenv("AWS_REGION")
S3_BUCKET = os.getenv("AWS_BUCKET_NAME")

s3 = boto3.client(
    "s3",
    region_name=AWS_REGION,
    aws_access_key_id=AWS_ACCESS_KEY_ID,
    aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
)

def upload_file_obj(file_obj, file_path):
    s3.upload_fileobj(file_obj, S3_BUCKET, file_path)

def download_file_obj(file_path):
    obj = s3.get_object(Bucket=S3_BUCKET, Key=file_path)
    return obj["Body"].read()

def generate_presigned_url(file_path, expiration=3600):
    return s3.generate_presigned_url(
        'get_object',
        Params={'Bucket': S3_BUCKET, 'Key': file_path},
        ExpiresIn=expiration
    )
