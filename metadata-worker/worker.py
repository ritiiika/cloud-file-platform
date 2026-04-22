import boto3
import json
import uuid
import os
import time
from datetime import datetime

print("🔥 Worker file loaded")  # Debug to ensure file runs

# AWS clients
sqs = boto3.client("sqs", region_name="us-east-1")
dynamodb = boto3.resource("dynamodb", region_name="us-east-1")

QUEUE_URL = os.getenv("QUEUE_URL")

if not QUEUE_URL:
    raise ValueError("QUEUE_URL is not set in environment variables")

# DynamoDB table
table = dynamodb.Table("FileMetadata")


def process_messages():
    print("🚀 Worker started")
    print("🔗 Queue URL:", QUEUE_URL)

    while True:
        try:
            print("\n👀 Checking queue...")

            response = sqs.receive_message(
                QueueUrl=QUEUE_URL,
                MaxNumberOfMessages=1,
                WaitTimeSeconds=10
            )

            messages = response.get("Messages", [])

            if not messages:
                print("📭 No messages in queue")
                time.sleep(2)
                continue

            for message in messages:
                try:
                    print("📩 Message received")

                    # Parse message
                    body = json.loads(message["Body"])
                    print("📦 Message body:", body)

                    # 🔴 VALIDATION (important for DLQ test)
                    if not body.get("file_name"):
                        raise Exception("Invalid message format: file_name missing")

                    # Prepare item
                    item = {
                        "fileID": str(uuid.uuid4()),
                        "fileName": body.get("file_name"),
                        "fileSize": body.get("file_size"),
                        "bucket": body.get("bucket"),
                        "uploadTime": datetime.utcnow().isoformat()
                    }

                    # Save to DynamoDB
                    table.put_item(Item=item)
                    print("✅ Stored in DynamoDB:", item["fileID"])

                    # ✅ DELETE ONLY ON SUCCESS
                    sqs.delete_message(
                        QueueUrl=QUEUE_URL,
                        ReceiptHandle=message["ReceiptHandle"]
                    )
                    print("🗑️ Message deleted from queue")

                except Exception as e:
                    print("❌ Processing failed:", str(e))
                    print("⚠️ Message NOT deleted → will retry / go to DLQ")
                    # 🚨 DO NOTHING → SQS retry handles it

        except Exception as outer_error:
            print("🔥 Worker loop error:", str(outer_error))
            time.sleep(5)  # prevent crash loop


# 🔥 ENTRY POINT (CRITICAL)
if __name__ == "__main__":
    process_messages()