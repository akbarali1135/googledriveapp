import os
import io
import json
from flask import Flask, request, jsonify
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

def get_drive_service():
    credentials_dict = {
        "type": os.getenv("GOOGLE_TYPE"),
        "project_id": os.getenv("GOOGLE_PROJECT_ID"),
        "private_key_id": os.getenv("GOOGLE_PRIVATE_KEY_ID"),
        "private_key": os.getenv("GOOGLE_PRIVATE_KEY").replace("\\n", "\n"),
        "client_email": os.getenv("GOOGLE_CLIENT_EMAIL"),
        "client_id": os.getenv("GOOGLE_CLIENT_ID"),
        "token_uri": "https://oauth2.googleapis.com/token"
    }
    creds = service_account.Credentials.from_service_account_info(credentials_dict)
    service = build("drive", "v3", credentials=creds)
    return service

@app.route("/upload", methods=["POST"])
def upload_file():
    if 'file' not in request.files:
        return jsonify({"error": "No file uploaded"}), 400

    file = request.files['file']
    drive_service = get_drive_service()

    file_metadata = {"name": file.filename}
    media = MediaIoBaseUpload(file.stream, mimetype=file.mimetype)

    uploaded_file = drive_service.files().create(
        body=file_metadata,
        media_body=media,
        fields="id"
    ).execute()

    file_id = uploaded_file.get("id")

    # Make file public
    drive_service.permissions().create(
        fileId=file_id,
        body={"role": "reader", "type": "anyone"},
    ).execute()

    file_url = f"https://drive.google.com/file/d/{file_id}/view?usp=sharing"
    return jsonify({"file_url": file_url})

# Needed for Vercel
app_handler = app
