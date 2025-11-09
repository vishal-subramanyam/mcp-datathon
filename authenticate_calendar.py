# authenticate_calendar.py
"""One-time script to authenticate with Google Calendar API and generate calendar_token.json"""

import os
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

SCOPES = ['https://www.googleapis.com/auth/calendar']

def authenticate():
    """Authenticate and create calendar_token.json file."""
    creds = None
    token_path = os.getenv("CALENDAR_TOKEN_PATH", "calendar_token.json")
    credentials_path = os.getenv("CALENDAR_CREDENTIALS_PATH", "credentials.json")
    
    # Try to load from .env file
    try:
        from dotenv import load_dotenv
        load_dotenv()
        token_path = os.getenv("CALENDAR_TOKEN_PATH", token_path)
        credentials_path = os.getenv("CALENDAR_CREDENTIALS_PATH", credentials_path)
    except ImportError:
        pass
    
    # Check if token already exists
    if os.path.exists(token_path):
        print(f"Token file already exists at {token_path}")
        print("If you want to re-authenticate, delete the token file first.")
        creds = Credentials.from_authorized_user_file(token_path, SCOPES)
        if creds.valid:
            print("✅ Existing token is valid. No need to re-authenticate.")
            return
        elif creds.expired and creds.refresh_token:
            print("Token expired. Refreshing...")
            creds.refresh(Request())
            with open(token_path, 'w') as token:
                token.write(creds.to_json())
            print("✅ Token refreshed successfully!")
            return
    
    # Check for credentials file
    if not os.path.exists(credentials_path):
        print(f"❌ Error: credentials.json not found at {credentials_path}")
        print("Please download credentials.json from Google Cloud Console.")
        print("Note: You can use the same credentials.json file used for Gmail API.")
        return
    
    print(f"Starting OAuth authentication for Google Calendar API...")
    print(f"Credentials file: {credentials_path}")
    print(f"Token will be saved to: {token_path}")
    print("\nA browser window will open for authentication...")
    
    # Start OAuth flow with a fixed port (8080)
    # Make sure http://localhost:8080/ is added as a redirect URI in Google Cloud Console
    flow = InstalledAppFlow.from_client_secrets_file(credentials_path, SCOPES)
    creds = flow.run_local_server(port=8080, prompt='consent')
    
    # Save the credentials
    with open(token_path, 'w') as token:
        token.write(creds.to_json())
    
    print(f"\n✅ Authentication successful!")
    print(f"✅ Token saved to {token_path}")
    print("\nYou can now use the Calendar MCP server.")

if __name__ == "__main__":
    authenticate()

