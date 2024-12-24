from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from googleapiclient.http import MediaFileUpload, MediaIoBaseDownload
from oauth2client.service_account import ServiceAccountCredentials
import io

def authenticate_drive(credentials_json):
    creds = ServiceAccountCredentials.from_json_keyfile_name(credentials_json, ["https://www.googleapis.com/auth/drive"])
    drive_service = build('drive', 'v3', credentials=creds)
    return drive_service

def upload_certificate(drive_service, folder_id, file_path, file_name):
    file_metadata = {
        'name': file_name,
        'parents': [folder_id]
    }
    media = MediaFileUpload(file_path, mimetype='application/pdf')
    file = drive_service.files().create(body=file_metadata, media_body=media, fields='id,webViewLink').execute()
    file_id = file.get('id')

    # Grant editor access to the email address
    permission = {
        'type': 'anyone',
        'role': 'writer'
    }
    drive_service.permissions().create(fileId=file_id, body=permission).execute()

    # Get the file link
    file_link = f"https://drive.google.com/file/d/{file_id}/view"

    return file_link

def download_file_from_drive(drive_service, file_id, local_path):
    request = drive_service.files().get_media(fileId=file_id)
    fh = io.FileIO(local_path, 'wb')
    downloader = MediaIoBaseDownload(fh, request)
    done = False
    while done is False:
        status, done = downloader.next_chunk()
        print("Download %d%%." % int(status.progress() * 100))
    print("Download complete!")

