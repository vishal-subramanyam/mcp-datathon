# Gmail MCP Server Setup Guide

## Overview
This Gmail MCP server allows you to read, send, and filter emails through the Gmail API using OAuth2 authentication.

## Prerequisites
1. A Google account with Gmail
2. Google Cloud Console access
3. Python 3.7+

## Setup Steps

### 1. Enable Gmail API in Google Cloud Console

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select an existing one
3. Navigate to **APIs & Services** > **Library**
4. Search for "Gmail API" and enable it

### 2. Create OAuth 2.0 Credentials

1. Navigate to **APIs & Services** > **Credentials**
2. Click **Create Credentials** > **OAuth client ID**
3. If prompted, configure the OAuth consent screen:
   - User Type: **External** (for personal use) or **Internal** (for Google Workspace)
   - Fill in the required app information
   - Add your email to test users (if using External)
4. For Application type, select **Desktop app**
5. Give it a name (e.g., "Gmail MCP Server")
6. Click **Create**
7. Download the credentials file and save it as `credentials.json` in the project directory

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure Environment Variables (Optional)

You can set these environment variables to customize paths:

```bash
# Path to credentials.json (default: credentials.json)
export GMAIL_CREDENTIALS_PATH="path/to/credentials.json"

# Path to token.json (default: token.json)
export GMAIL_TOKEN_PATH="path/to/token.json"
```

Or add them to a `.env` file:
```
GMAIL_CREDENTIALS_PATH=credentials.json
GMAIL_TOKEN_PATH=token.json
```

### 5. First Run Authentication

1. Run the server:
   ```bash
   python gmail_mcp_server.py
   ```

2. On first run, a browser window will open for OAuth2 authentication
3. Sign in with your Google account and grant permissions
4. A `token.json` file will be created automatically (this stores your access/refresh tokens)
5. Subsequent runs will use the saved token (no need to re-authenticate unless it expires)

## Usage

### Available Tools

1. **list_emails** - List emails with optional Gmail search query
   - Query examples:
     - `is:unread` - Unread emails
     - `from:example@gmail.com` - Emails from specific sender
     - `subject:test` - Emails with "test" in subject
     - `has:attachment` - Emails with attachments
     - `after:2024-01-01` - Emails after a date

2. **get_email** - Get detailed information about a specific email

3. **send_email** - Send an email through Gmail

4. **search_emails** - Advanced email search with multiple filters

5. **mark_email_read** - Mark an email as read

6. **mark_email_unread** - Mark an email as unread

7. **delete_email** - Delete an email

### Gmail Search Query Syntax

The server supports Gmail's powerful search syntax:
- `from:email@example.com` - From specific sender
- `to:email@example.com` - To specific recipient
- `subject:keyword` - Subject contains keyword
- `has:attachment` - Has attachments
- `is:unread` - Unread emails
- `is:read` - Read emails
- `is:starred` - Starred emails
- `after:YYYY-MM-DD` - After date
- `before:YYYY-MM-DD` - Before date
- `larger:10M` - Larger than 10MB
- `filename:pdf` - Has PDF attachment

Combine multiple terms with spaces (AND) or use `OR` for OR logic.

## Security Notes

- **Never commit `credentials.json` or `token.json` to version control**
- These files are already in `.gitignore`
- `token.json` contains your access and refresh tokens - keep it secure
- If your token is compromised, revoke access in [Google Account Security](https://myaccount.google.com/security)

## Troubleshooting

### "Credentials not found" error
- Ensure `credentials.json` is in the project directory
- Or set `GMAIL_CREDENTIALS_PATH` environment variable

### "Access denied" or "Permission denied" error
- Check that Gmail API is enabled in Google Cloud Console
- Verify OAuth consent screen is configured
- Ensure you've granted the necessary permissions during authentication

### Token expired
- Delete `token.json` and run the server again to re-authenticate
- The server will automatically refresh tokens if a refresh token is available

### Rate Limits
- Gmail API has rate limits (250 units per user per second)
- If you hit rate limits, the server will return an error
- Wait a moment and try again

## File Structure

```
.
├── gmail_mcp_server.py    # Gmail MCP server
├── credentials.json        # OAuth2 credentials (download from Google Cloud Console)
├── token.json             # Access/refresh tokens (created automatically)
├── requirements.txt       # Python dependencies
└── GMAIL_SETUP.md        # This file
```

## Additional Resources

- [Gmail API Documentation](https://developers.google.com/gmail/api)
- [Gmail API Python Quickstart](https://developers.google.com/gmail/api/quickstart/python)
- [Gmail Search Operators](https://support.google.com/mail/answer/7190)

