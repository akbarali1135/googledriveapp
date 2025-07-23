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

        # Save file to temporary location
        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            uploaded_file.save(tmp.name)
            tmp.flush()

            # Build client config from environment variables
            client_config = {
                "installed": {
                    "client_id": os.environ["G_CLIENT_ID"],
                    "client_secret": os.environ["G_CLIENT_SECRET"],
                    "auth_uri": os.environ.get("G_AUTH_URI"),
                    "token_uri": os.environ.get("G_TOKEN_URI"),
                    "redirect_uris": [
                        "urn:ietf:wg:oauth:2.0:oob",
                        "http://localhost"
                    ]
                }
            }

            # Save client config to temporary file for PyDrive
            with tempfile.NamedTemporaryFile(delete=False, mode="w") as cred_file:
                json.dump(client_config, cred_file)
                cred_file_path = cred_file.name

            # Authenticate
            gauth = GoogleAuth()
            gauth.LoadClientConfigFile(cred_file_path)

            # Try loading saved credentials from temp (not persisted in serverless)
            if gauth.credentials is None:
                gauth.LocalWebserverAuth()  # This requires manual login; not usable on Vercel
            elif gauth.access_token_expired:
                gauth.Refresh()
            else:
                gauth.Authorize()

            drive = GoogleDrive(gauth)

            # Upload to Google Drive
            file_drive = drive.CreateFile({'title': uploaded_file.filename})
            file_drive.SetContentFile(tmp.name)
            file_drive.Upload()

            # Make file publicly accessible
            file_drive.InsertPermission({
                'type': 'anyone',
                'value': 'anyone',
                'role': 'reader'
            })

            os.unlink(tmp.name)
            return jsonify({"url": file_drive['alternateLink']}), 200

    return jsonify({"error": "Only POST method supported"}), 405
