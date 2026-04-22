from fastapi import FastAPI, UploadFile, File
from fastapi.responses import StreamingResponse
import boto3
import json
import os

app = FastAPI()

# AWS clients
s3 = boto3.client("s3", region_name="us-east-1")
sqs = boto3.client("sqs", region_name="us-east-1")

BUCKET_NAME = "file-processing-bucket000"

# Read from environment
QUEUE_URL = os.getenv("QUEUE_URL")


@app.get("/")
def home():
    return {"message": "Upload Service Running 🚀"}


# ✅ UPLOAD API (FIXED + DEBUG)
@app.post("/upload_file")
async def upload_file(file: UploadFile = File(...)):
    try:
        print("📥 Upload request received")

        contents = await file.read()

        # Upload to S3
        s3.put_object(
            Bucket=BUCKET_NAME,
            Key=file.filename,
            Body=contents
        )
        print("✅ Uploaded to S3")

        metadata = {
            "file_name": file.filename,
            "file_size": len(contents),
            "bucket": BUCKET_NAME
        }

        print("📦 Metadata prepared:", metadata)
        print("🔗 QUEUE_URL:", QUEUE_URL)

        # Validate QUEUE_URL
        if not QUEUE_URL:
            raise ValueError("QUEUE_URL is missing in environment variables")

        # Send to SQS
        response = sqs.send_message(
            QueueUrl=QUEUE_URL,
            MessageBody=json.dumps(metadata)
        )

        print("✅ Message sent to SQS:", response)

        return {
            "message": "File uploaded successfully",
            "status": "Metadata sent to queue"
        }

    except Exception as e:
        print("❌ ERROR:", str(e))  # VERY IMPORTANT
        return {
            "message": "Upload failed",
            "error": str(e)
        }


# ✅ GET FILE
@app.get("/get_file/{file_name}")
def get_file(file_name: str):
    try:
        response = s3.get_object(
            Bucket=BUCKET_NAME,
            Key=file_name
        )

        return StreamingResponse(
            response["Body"],
            media_type="application/octet-stream"
        )

    except Exception as e:
        print("❌ ERROR:", str(e))
        return {"error": str(e)}


# ✅ DELETE FILE
@app.delete("/delete_file/{file_name}")
def delete_file(file_name: str):
    try:
        s3.delete_object(
            Bucket=BUCKET_NAME,
            Key=file_name
        )

        print("🗑️ File deleted from S3")

        return {"message": "File deleted from S3"}

    except Exception as e:
        print("❌ ERROR:", str(e))
        return {"error": str(e)}