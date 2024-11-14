import os
import zipfile
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload
from googleapiclient.http import MediaFileUpload
from google.auth.transport.requests import Request

base_dir = os.path.dirname(__file__)
authorized_user_file = os.path.join(base_dir, 'token.json')
authorized_secrets_file = os.path.join(base_dir, 'client.json')
SCOPES = ['https://www.googleapis.com/auth/drive']
file_types = [
    "application/x-zip-compressed",
    "application/zip",
    "image/x-photoshop",
    "image/jpeg",
    "image/png",
    "image/jpg",
]
file_zip_types = file_types[0:2]
file_image_types = file_types[2:]


class GDriveProcessor:

    def __init__(self, download_folder_id, upload_folder_id, max_depth=15):
        self.download_folder_id = download_folder_id
        self.upload_folder_id = upload_folder_id
        self.service = self.authenticate_get_service()
        self.source_dir = os.path.join(base_dir, 'source')
        self.max_depth = max_depth

    def download_folder(self, folder_id=None, local_folder_path=None, depth=0):
        # Raise Exception if max depth
        if depth > self.max_depth:
            raise Exception('Maximum depth reached')

        # Create local folder
        folder_id = self.download_folder_id if folder_id is None else folder_id
        local_folder_path = self.source_dir if local_folder_path is None else local_folder_path
        folder_metadata = self.service.files().get(fileId=folder_id).execute()
        folder_name = folder_metadata.get('name')
        local_folder_path = os.path.join(local_folder_path, folder_name)
        os.makedirs(local_folder_path, exist_ok=True)

        # List files in the current folder
        query = f"'{folder_id}' in parents and trashed = false"
        results = self.service.files().list(q=query).execute()
        items = results.get('files', [])

        for item in items:
            if item['mimeType'] == 'application/vnd.google-apps.folder':
                # Recursively download subfolders
                depth += 1
                self.download_folder(item['id'], local_folder_path, depth)
            else:
                # Download the file
                local_filepath = self._download_file(item['id'], item['name'], local_folder_path)
                if item['mimeType'] in file_zip_types:
                    self._extract_zip_file(local_filepath, local_folder_path)

    def upload_folder(self, folder_path, parent_id=None):
        folder_name = os.path.basename(folder_path)
        folder_id = self._create_folder(folder_name, parent_id)
        print(f'Create folder {folder_id}')
        if parent_id is None:
            self._make_upload_folder_public()
        for item in os.listdir(folder_path):
            item_path = os.path.join(folder_path, item)
            if os.path.isdir(item_path):
                self.upload_folder(folder_path=item_path, parent_id=folder_id)
            else:
                self._upload_file_to_gdrive_folder(file_path=item_path, folder_id=folder_id)
        return folder_id

    def _make_upload_folder_public(self):
        # Define the permissions
        permissions = {
            'type': 'anyone',
            'role': 'reader'  # Use 'writer' for edit access
        }

        # Apply the permission to the folder
        self.service.permissions().create(
            fileId=self.upload_folder_id,
            body=permissions,
            fields='id'
        ).execute()

    def _upload_file_to_gdrive_folder(self, file_path, folder_id=None):
        file_name = os.path.basename(file_path)
        file_metadata = {
            'name': file_name,
            'parents': [folder_id]
        }
        media = MediaFileUpload(file_path, resumable=True)
        file = self.service.files().create(body=file_metadata, media_body=media, fields='id').execute()
        return file.get('id')

    def _create_folder(self, folder_name, parent_id=None):
        file_metadata = {
            'name': folder_name,
            'mimeType': 'application/vnd.google-apps.folder'
        }
        if parent_id:
            file_metadata['parents'] = [parent_id]
        folder = self.service.files().create(body=file_metadata, fields='id').execute()
        return folder.get('id')

    @staticmethod
    def _extract_zip_file(zip_path, extract_to_folder):
        # Ensure the extraction directory exists
        os.makedirs(extract_to_folder, exist_ok=True)

        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(extract_to_folder)

    def _download_file(self, file_id, file_name, folder_path):
        request = self.service.files().get_media(fileId=file_id)
        local_filepath = os.path.join(folder_path, file_name)

        with open(local_filepath, 'wb') as fh:
            downloader = MediaIoBaseDownload(fh, request)
            done = False
            while done is False:
                status, done = downloader.next_chunk()
                print(f"Download {file_name}: {int(status.progress() * 100)}%.")
        return local_filepath

    @staticmethod
    def authenticate_get_service():
        creds = None
        if os.path.exists(authorized_user_file):
            creds = Credentials.from_authorized_user_file(authorized_user_file, SCOPES)

        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(
                    authorized_secrets_file, SCOPES
                )
                creds = flow.run_local_server(port=8080)  # This will open a browser to authenticate
            with open(authorized_user_file, 'w') as token:
                token.write(creds.to_json())

        service = build('drive', 'v3', credentials=creds)

        return service
