import os
import zipfile
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload
from googleapiclient.http import MediaFileUpload

base_dir = os.path.dirname(__file__)
source_dir = os.path.join(base_dir, 'source')

# Google Drive API credentials
SCOPES = ['https://www.googleapis.com/auth/drive']
SERVICE_ACCOUNT_FILE = os.path.join(base_dir, 'client_secret.json')

# Authenticate using service account credentials
credentials = service_account.Credentials.from_service_account_file(
    SERVICE_ACCOUNT_FILE, scopes=SCOPES
)

# Build the Google Drive API service
service = build('drive', 'v3', credentials=credentials)

FOLDER_SOURCE_ID = '1SyVSwqNb7AtBPcDY8Fq5oy1XnzLFhGtI'


class GDriveProcessor:

    scopes = ['https://www.googleapis.com/auth/drive']
    authorized_user_file = os.path.join(base_dir, 'token.json')
    credentials = service_account.Credentials.with_token_uri(
        SERVICE_ACCOUNT_FILE, scopes=SCOPES
    )
    service = build('drive', 'v3', credentials=credentials)

    def __init__(self, folder_id):
        self.folder_id = folder_id


def download_folder(folder_id="1WTdCCide6UcwB8p26XZYkV-mvBzno97X", source_dir=source_dir, service=service):
    # Create local folder
    folder_metadata = service.files().get(fileId=folder_id).execute()
    folder_name = folder_metadata.get('name')
    local_folder_path = os.path.join(source_dir, folder_name)
    os.makedirs(local_folder_path, exist_ok=True)

    # List files in the current folder
    query = f"'{folder_id}' in parents and trashed = false"
    results = service.files().list(q=query).execute()
    items = results.get('files', [])

    for item in items:
        if item['mimeType'] == 'application/vnd.google-apps.folder':
            # Recursively download subfolders
            download_folder(item['id'], local_folder_path)
        else:
            # Download the file
            download_file(item['id'], item['name'], local_folder_path)


def download_file(file_id, file_name, folder_path, service=service):
    request = service.files().get_media(fileId=file_id)
    local_filepath = os.path.join(folder_path, file_name)

    with open(local_filepath, 'wb') as fh:
        downloader = MediaIoBaseDownload(fh, request)
        done = False
        while done is False:
            status, done = downloader.next_chunk()
            print(f"Download {file_name}: {int(status.progress() * 100)}%.")


def authenticate_and_download_zip(source_dir, file_id):

    # Fetch the file metadata
    file = service.files().get(fileId=file_id, fields='name').execute()
    # Extract the file name
    file_name = file.get('name')

    # Download the ZIP file
    request = service.files().get_media(fileId=file_id)

    save_unzip_file = os.path.join(source_dir, file_name)
    save_zip_path = os.path.join(source_dir, file_name.split('.')[0])

    if os.path.exists(save_unzip_file):
        return save_zip_path

    with open(save_unzip_file, 'wb') as fh:
        downloader = MediaIoBaseDownload(fh, request)
        done = False
        while done is False:
            status, done = downloader.next_chunk()
            print(f"Download {file_name}: {int(status.progress() * 100)}%.")

    extract_zip_file(save_unzip_file, save_zip_path)

    return save_zip_path  # the folder unzip path


def get_file_ids_from_google_drive_folder(folder_id):

    # Query to find files in the specific folder
    query = f"'{folder_id}' in parents"

    # Call the Drive v3 API
    results = service.files().list(
        q=query, spaces='drive',
        fields="nextPageToken, files(id, name)"
    ).execute()

    return results.get('files', [])


def upload_folder(folder_path, service=service, parent_id=None):
    folder_name = os.path.basename(folder_path)
    folder_id = create_folder(service, folder_name, parent_id)
    print(f'Create folder {folder_id}')
    make_folder_public(folder_id)
    print(f'Folder Path {folder_path}')
    for item in os.listdir(folder_path):
        item_path = os.path.join(folder_path, item)
        if os.path.isdir(item_path):
            upload_folder(folder_path=item_path, service=service, parent_id=folder_id)
        else:
            upload_file_to_folder(file_path=item_path, service=service, folder_id=folder_id)
    return folder_id


def extract_zip_file(zip_path, extract_to_folder):
    # Ensure the extraction directory exists
    os.makedirs(extract_to_folder, exist_ok=True)

    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
        # Extract all the contents into the directory
        zip_ref.extractall(extract_to_folder)


def create_folder(service, folder_name, parent_id="1HQwa_JwBFhBD-kJoQs2L6wk1gmwcevvx"):
    # def create_folder(service, folder_name, parent_id=None):
    file_metadata = {
        'name': folder_name,
        'mimeType': 'application/vnd.google-apps.folder'
    }
    if parent_id:
        file_metadata['parents'] = [parent_id]
    folder = service.files().create(body=file_metadata, fields='id').execute()
    return folder.get('id')


def upload_file_to_folder(file_path, service, folder_id):
    file_name = os.path.basename(file_path)
    file_metadata = {
        'name': file_name,
        'parents': [folder_id]
    }
    media = MediaFileUpload(file_path, resumable=True)
    file = service.files().create(body=file_metadata, media_body=media, fields='id').execute()
    return file.get('id')


def make_folder_public(folder_id, service=service):
    # Define the permissions
    permissions = {
        'type': 'anyone',
        'role': 'reader'  # Use 'writer' for edit access
    }

    # Apply the permission to the folder
    service.permissions().create(
        fileId=folder_id,
        body=permissions,
        fields='id'
    ).execute()

    print(f'Folder {folder_id} is now public.')


download_folder()
