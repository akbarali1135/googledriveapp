import os
import json
import tempfile
from flask import Request, jsonify
from pydrive.auth import GoogleAuth
from pydrive.drive import GoogleDrive

def handler(request: Request):
    if request.method == "POST":
        uploaded_file = request.files.get("file")
        if uploaded_file is None or uploaded_file.filename == '':
            return jsonify({"error": "No file uploaded"}), 400

        # Save to a temporary file
        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            uploaded_file.save(tmp.name)
            tmp.flush()

            # Auth Google Drive
            gauth = GoogleAuth()
            gauth.LoadCredentialsFile("client_secrets.json")
            if gauth.credentials is None:
                gauth.LocalWebserverAuth()
            elif gauth.access_token_expired:
                gauth.Refresh()
            else:
                gauth.Authorize()
            gauth.SaveCredentialsFile("client_secrets.json")

            drive = GoogleDrive(gauth)

            # Upload
            file_drive = drive.CreateFile({'title': uploaded_file.filename})
            file_drive.SetContentFile(tmp.name)
            file_drive.Upload()

            # Shareable link
            file_drive.InsertPermission({
                'type': 'anyone',
                'value': 'anyone',
                'role': 'reader'
            })

            os.unlink(tmp.name)
            return jsonify({"url": file_drive['alternateLink']}), 200

    return jsonify({"error": "Only POST method supported"}), 405
