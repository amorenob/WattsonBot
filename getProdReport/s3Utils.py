import boto3
import random
import uuid
from typing import Any, Dict

def getGetterSignedUrl(bucket: str, key: str) -> str:
    s3 = boto3.client('s3')
    url = s3.generate_presigned_url('get_object', Params={'Bucket': bucket, 'Key': key})
    return url

def getUploaderSignedUrl(bucket: str, key: str) -> str:
    s3 = boto3.client('s3')
    url = s3.generate_presigned_url('put_object', Params={'Bucket': bucket, 'Key': key})
    return url

def savePdfInS3(pdf: bytes, bucket: str, key: str) -> str:
    s3 = boto3.client('s3')
    s3.put_object(Bucket=bucket, Key=key, Body=pdf, ContentType='application/pdf')
    return f"https://{bucket}.s3.amazonaws.com/{key}"

def saveDocxInS3(docx: bytes, bucket: str, key: str) -> str:
    s3 = boto3.client('s3')
    s3.put_object(Bucket=bucket, Key=key, Body=docx, ContentType='application/vnd.openxmlformats-officedocument.wordprocessingml.document')
    return f"https://{bucket}.s3.amazonaws.com/{key}"

def getReportKey(userId: str, conversarionId: str, extension: str) -> str:
    ramdom_int = random.randint(0, 1000000)
    return f"{userId}/{conversarionId}/reports/{ramdom_int}.{extension}"

def getRandomPdfKey(userId: str, conversarionId: str) -> str:
    extension = 'pdf'
    uuid_str = str(uuid.uuid4())
    return f"{userId}/{conversarionId}/reports/{uuid_str}.{extension}"

# change metadata content type to application/pdf
def changeMetadata(bucket: str, key: str) -> None:
    s3 = boto3.client('s3')
    s3.copy_object(Bucket=bucket, Key=key, CopySource=f"{bucket}/{key}", MetadataDirective='REPLACE', ContentType='application/pdf')