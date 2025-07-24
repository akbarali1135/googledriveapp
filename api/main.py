# api/main.py
import os
import uuid
import shutil
from fastapi import FastAPI, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

app = FastAPI()

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Load credentials from ENV
service_account_info = {
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

credentials = service_account.Credentials.from_service_account_info(
    service_account_info,
    scopes=["https://www.googleapis.com/auth/drive"]
)
drive_service = build("drive", "v3", credentials=credentials)

@app.post("/upload/")
async def upload_to_drive(file: UploadFile = File(...)):
    temp_file_path = f"/tmp/{uuid.uuid4()}_{file.filename}"
    with open(temp_file_path, "wb") as f:
        shutil.copyfileobj(file.file, f)

    file_metadata = {'name': file.filename}
    media = MediaFileUpload(temp_file_path, resumable=True)

    uploaded_file = drive_service.files().create(
        body=file_metadata,
        media_body=media,
        fields='id'
    ).execute()

    file_id = uploaded_file.get('id')

    # Make public
    drive_service.permissions().create(
        fileId=file_id,
        body={'type': 'anyone', 'role': 'reader'},
    ).execute()

    shareable_url = f"https://drive.google.com/file/d/{file_id}/view?usp=sharing"
    os.remove(temp_file_path)

    return JSONResponse({"url": shareable_url})
