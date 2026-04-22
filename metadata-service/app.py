from fastapi import FastAPI
import boto3
import uuid
from datetime import datetime

app = FastAPI()

dynamodb = boto3.resource("dynamodb", region_name="us-east-1")
table = dynamodb.Table("FileMetadata")


@app.get("/")
def home():
    return {"message": "Metadata Service Running 🚀"}


# ✅ STORE METADATA
@app.post("/store_metadata")
def store_metadata(file_name: str, file_size: int, bucket: str):
    try:
        item = {
            "fileID": str(uuid.uuid4()),
            "fileName": file_name,
            "fileSize": file_size,
            "bucket": bucket,
            "uploadTime": str(datetime.utcnow())
        }

        table.put_item(Item=item)

        return {
            "message": "Metadata stored successfully",
            "data": item
        }

    except Exception as e:
        return {"error": str(e)}


# ✅ LIST FILES
@app.get("/files")
def list_files():
    try:
        response = table.scan()

        files = response.get("Items", [])

        return {
            "count": len(files),
            "files": files
        }

    except Exception as e:
        return {
            "error": "Failed to fetch files",
            "details": str(e)
        }

@app.delete("/files/{file_name}")
def delete_file_metadata(file_name: str):
    try:
        response = table.scan()

        for item in response.get("Items", []):
            if item["fileName"] == file_name:
                table.delete_item(
                    Key={"fileID": item["fileID"]}
                )
                return {"message": "Metadata deleted successfully"}

        return {"message": "File not found"}

    except Exception as e:
        return {
            "error": "Failed to delete metadata",
            "details": str(e)
        }
    


@app.get("/files/{file_name}")
def get_file(file_name: str):
    try:
        response = table.scan()

        for item in response.get("Items", []):
            if item["fileName"] == file_name:
                return item

        return {"message": "File not found"}

    except Exception as e:
        return {
            "error": "Failed to fetch file",
            "details": str(e)
        }
@app.get("/search")
def search_files(file_name: str):
    try:
        response = table.scan()

        results = [
            item for item in response.get("Items", [])
            if file_name.lower() in item["fileName"].lower()
        ]

        return {
            "count": len(results),
            "results": results
        }

    except Exception as e:
        return {
            "error": "Search failed",
            "details": str(e)
        }