# import functions
import os
import pickle
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request

# request all access (permission to read/send/receive emails, manage the inbox, and more)
GMAIL_SCOPES = ["https://mail.google.com/"]
CALENDAR_SCOPES = ['https://www.googleapis.com/auth/calendar']

def authenticate(type):
    # pickle stores the user's access and refresh tokens, and is created automatically when the authorization flow completes for the first time
    creds = None
    if (type == "gmail"):
        file = "token_gmail.pickle"
        version = "v1"
    else:
        file = "token_gcal.pickle"
        version = "v3"
    
    # check pickle file
    if os.path.exists(file):
        with open(file, "rb") as token:
            creds = pickle.load(token)
    
    # if no credentials available, let the user log in
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            if (type == "gmail"):
                flow = InstalledAppFlow.from_client_secrets_file('credentials.json', GMAIL_SCOPES)
            else:
                flow = InstalledAppFlow.from_client_secrets_file('credentials.json', CALENDAR_SCOPES)
            creds = flow.run_local_server(port=0)

        # save credentials for next run
        with open(file, "wb") as token:
            pickle.dump(creds, token)
    
    # return the service
    return build(type, version, credentials=creds)