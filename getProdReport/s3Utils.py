import random
import uuid
import logging
from typing import Any, Dict
import boto3
from botocore.exceptions import ClientError

# Set up logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

def getGetterSignedUrl(bucket: str, key: str) -> str:
    try:
        s3 = boto3.client('s3')
        url = s3.generate_presigned_url('get_object', Params={'Bucket': bucket, 'Key': key})
        logger.info(f"Signed URL generated successfully for bucket: {bucket}, key: {key}")
        return url
    except ClientError as e:
        logger.error(f"Error generating signed URL: {e}")
        raise e

def getUploaderSignedUrl(bucket: str, key: str) -> str:
    try:
        s3 = boto3.client('s3')
        url = s3.generate_presigned_url('put_object', Params={'Bucket': bucket, 'Key': key})
        logger.info(f"Signed URL generated successfully for bucket: {bucket}, key: {key}")
        return url
    except ClientError as e:
        logger.error(f"Error generating signed URL: {e}")
        raise e

def savePdfInS3(pdf: bytes, bucket: str, key: str) -> str:
    try:
        s3 = boto3.client('s3')
        s3.put_object(Bucket=bucket, Key=key, Body=pdf, ContentType='application/pdf')
        logger.info(f"PDF saved successfully to S3 bucket: {bucket}, key: {key}")
        return f"https://{bucket}.s3.amazonaws.com/{key}"
    except ClientError as e:
        logger.error(f"Error saving PDF to S3: {e}")
        raise e

def saveDocxInS3(docx: bytes, bucket: str, key: str) -> str:
    try:
        s3 = boto3.client('s3')
        s3.put_object(Bucket=bucket, Key=key, Body=docx, ContentType='application/vnd.openxmlformats-officedocument.wordprocessingml.document')
        logger.info(f"Docx saved successfully to S3 bucket: {bucket}, key: {key}")
        return f"https://{bucket}.s3.amazonaws.com/{key}"
    except ClientError as e:
        logger.error(f"Error saving Docx to S3: {e}")
        raise e

def getReportKey(userId: str, conversarionId: str, extension: str) -> str:
    ramdom_int = random.randint(0, 1000000)
    return f"{userId}/{conversarionId}/reports/{ramdom_int}.{extension}"

def getRandomPdfKey(userId: str, conversarionId: str) -> str:
    extension = 'pdf'
    uuid_str = str(uuid.uuid4())
    return f"{userId}/{conversarionId}/reports/{uuid_str}.{extension}"

# change metadata content type to application/pdf
def changeMetadata(bucket: str, key: str) -> None:
    try:
        s3 = boto3.client('s3')
        s3.copy_object(Bucket=bucket, Key=key, CopySource=f"{bucket}/{key}", MetadataDirective='REPLACE', ContentType='application/pdf')
        logger.info(f"Metadata changed successfully for bucket: {bucket}, key: {key}")
    except ClientError as e:
        logger.error(f"Error changing metadata: {e}")
        raise e
