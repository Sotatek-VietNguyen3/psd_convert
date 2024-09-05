import os
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request

# Scopes specify what your application is authorized to do (modify if needed)
SCOPES = ['https://www.googleapis.com/auth/drive']


def authenticate_google_drive():
    creds = None
    # Check if token.json already exists (this stores access/refresh tokens)
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)

    # If there are no valid credentials available, prompt the user to log in
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            # The first time the flow runs, credentials.json is needed
            flow = InstalledAppFlow.from_client_secrets_file(
                'client.json', SCOPES
            )
            creds = flow.run_local_server(port=8080)  # This will open a browser to authenticate
        # Save the credentials for the next run by creating token.json
        with open('token.json', 'w') as token:
            token.write(creds.to_json())

    # The credentials can now be used for further API requests
    return creds


# Authenticate and create token.json if it doesn't exist
if __name__ == '__main__':
    creds = authenticate_google_drive()
    print("Authentication successful, token.json created!")
