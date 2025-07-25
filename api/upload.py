from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import os
import io
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/")
async def upload_to_drive(file: UploadFile = File(...)):
    try:
        content = await file.read()

        credentials_dict = {
            "type": os.getenv("GDRIVE_TYPE"),
            "project_id": os.getenv("GDRIVE_PROJECT_ID"),
            "private_key_id": os.getenv("GDRIVE_PRIVATE_KEY_ID"),
            "private_key": os.getenv("GDRIVE_PRIVATE_KEY").replace("\\n", "\n"),
            "client_email": os.getenv("GDRIVE_CLIENT_EMAIL"),
            "client_id": os.getenv("GDRIVE_CLIENT_ID"),
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
            "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
            "client_x509_cert_url": "https://www.googleapis.com/robot/v1/metadata/x509/fastapi-drive-uploader%40chichas-app.iam.gserviceaccount.com",
            "universe_domain": "googleapis.com"
        }

        credentials = service_account.Credentials.from_service_account_info(credentials_dict)
        service = build("drive", "v3", credentials=credentials)

        file_metadata = {"name": file.filename}
        media = MediaIoBaseUpload(io.BytesIO(content), mimetype=file.content_type)

        uploaded_file = service.files().create(
            body=file_metadata,
            media_body=media,
            fields="id"
        ).execute()

        file_id = uploaded_file.get("id")
        service.permissions().create(
            fileId=file_id,
            body={"role": "reader", "type": "anyone"},
        ).execute()

        file_link = f"https://drive.google.com/file/d/{file_id}/view"
        return {"link": file_link}

    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})
