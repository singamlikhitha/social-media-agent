import os
import json
from google_auth_oauthlib.flow import InstalledAppFlow
from google.oauth2.credentials import Credentials

SCOPES = [
    "https://www.googleapis.com/auth/youtube.upload",
    "https://www.googleapis.com/auth/youtube.readonly",
    "https://www.googleapis.com/auth/youtube.force-ssl",
]


def print_youtube_guide():
    print("""
=== YouTube Data API v3 Setup Guide ===

Step 1: Create a Google Cloud Project
  - Go to https://console.cloud.google.com/
  - Click "Select a project" -> "New Project"
  - Name it (e.g., "Social Media Agent")

Step 2: Enable YouTube Data API v3
  - Go to "APIs & Services" -> "Library"
  - Search for "YouTube Data API v3"
  - Click "Enable"

Step 3: Create OAuth 2.0 Credentials
  - Go to "APIs & Services" -> "Credentials"
  - Click "Create Credentials" -> "OAuth client ID"
  - Application type: "Desktop app"
  - Download the JSON file

Step 4: Configure OAuth Consent Screen
  - Go to "APIs & Services" -> "OAuth consent screen"
  - Choose "External" user type
  - Fill in app name, support email
  - Add scopes: youtube.upload, youtube.readonly, youtube.force-ssl
  - Add your email as a test user

Step 5: Place the credentials file
  - Save the downloaded JSON as "client_secrets.json" in the project root

Step 6: Run this wizard to complete OAuth flow
  - We'll open a browser for you to authorize access
""")


def run_oauth_flow(client_secrets_file: str, token_file: str) -> bool:
    if not os.path.exists(client_secrets_file):
        print(f"Error: {client_secrets_file} not found.")
        print("Download it from Google Cloud Console and place it in the project root.")
        return False

    try:
        flow = InstalledAppFlow.from_client_secrets_file(client_secrets_file, SCOPES)
        credentials = flow.run_local_server(port=8090)

        with open(token_file, "w") as f:
            f.write(credentials.to_json())

        print(f"YouTube OAuth token saved to {token_file}")
        return True

    except Exception as e:
        print(f"OAuth flow failed: {e}")
        return False
