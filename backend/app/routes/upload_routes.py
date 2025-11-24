from fastapi import APIRouter, UploadFile, File, Depends, HTTPException
from ..db import SessionLocal
from ..config import settings
import boto3
import uuid

router = APIRouter(prefix="/upload", tags=["upload"])

# Use Minio
# s3 = boto3.client(
#     "s3",
#     endpoint_url=settings.S3_ENDPOINT,
#     aws_access_key_id=settings.S3_ACCESS_KEY,
#     aws_secret_access_key=settings.S3_SECRET_KEY,
# )

# Use AWS S3
s3 = boto3.client(
    "s3",
    aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
    aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
    region_name=settings.AWS_REGION,  # e.g., "us-east-1"
)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.post("/image")
def upload_image(file: UploadFile = File(...)):
    import traceback
    key = f"images/{uuid.uuid4().hex}_{file.filename}"
    try:
        s3.upload_fileobj(file.file, settings.S3_BUCKET, key)

        # Minio url
        # url = f"{settings.S3_ENDPOINT}/{settings.S3_BUCKET}/{key}"

        # AWS S3 public URL (or pre-signed URL if private)
        url = f"https://{settings.S3_BUCKET}.s3.{settings.AWS_REGION}.amazonaws.com/{key}"


        return {"url": url}
    except Exception as e:
        print("Upload error:", e)
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Upload failed: {e}")



