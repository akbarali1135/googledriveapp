from flask import Flask, request, jsonify
import os
import tempfile
import json
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

app = Flask(__name__)

# Setup Google Drive API
SERVICE_ACCOUNT_FILE = os.path.join(os.path.dirname(__file__), '..', 'service_account.json')
SCOPES = ['https://www.googleapis.com/auth/drive.file']

credentials = service_account.Credentials.from_service_account_file(
    SERVICE_ACCOUNT_FILE, scopes=SCOPES
)
drive_service = build('drive', 'v3', credentials=credentials)

@app.route('/api/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({"error": "No file uploaded"}), 400

    file = request.files['file']
    with tempfile.NamedTemporaryFile(delete=False) as tmp:
        file.save(tmp.name)

        # Upload to Google Drive
        file_metadata = {'name': file.filename}
        media = MediaFileUpload(tmp.name, mimetype='application/pdf')
        uploaded_file = drive_service.files().create(
            body=file_metadata,
            media_body=media,
            fields='id'
        ).execute()

        # Make file public
        drive_service.permissions().create(
            fileId=uploaded_file['id'],
            body={'type': 'anyone', 'role': 'reader'}
        ).execute()

        file_url = f"https://drive.google.com/file/d/{uploaded_file['id']}/view?usp=sharing"
        return f"""
        <script>
            document.getElementById("urlBox").value = "{file_url}";
        </script>
        """
