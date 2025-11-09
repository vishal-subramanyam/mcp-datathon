# Google Calendar MCP Server Setup Guide

## Overview
This Google Calendar MCP server allows you to create, read, update, and delete calendar events through the Google Calendar API using OAuth2 authentication.

## Prerequisites
1. A Google account
2. Google Cloud Console access
3. Python 3.7+
4. **Same credentials.json file used for Gmail API** (you don't need separate credentials!)

## Setup Steps

### 1. Enable Calendar API in Google Cloud Console

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Select the same project you used for Gmail API (or create a new one)
3. Navigate to **APIs & Services** > **Library**
4. Search for "Calendar API" and enable it
5. **Important**: You can use the same OAuth 2.0 credentials you created for Gmail API!

### 2. Use Existing OAuth 2.0 Credentials

**Good news!** You can reuse the same `credentials.json` file you used for Gmail API. Just make sure:

1. The Calendar API is enabled in the same Google Cloud project
2. The OAuth consent screen includes Calendar API scope
3. Your test user email is already added (same as Gmail setup)

### 3. Install Dependencies

Dependencies should already be installed from Gmail setup:

```bash
pip install -r requirements.txt
```

If not, install:
```bash
pip install google-api-python-client google-auth-httplib2 google-auth-oauthlib
```

### 4. Configure Environment Variables (Optional)

You can set these environment variables to customize paths:

```bash
# Path to credentials.json (default: credentials.json)
export CALENDAR_CREDENTIALS_PATH="path/to/credentials.json"

# Path to calendar_token.json (default: calendar_token.json)
export CALENDAR_TOKEN_PATH="path/to/calendar_token.json"
```

Or add them to a `.env` file:
```
CALENDAR_CREDENTIALS_PATH=credentials.json
CALENDAR_TOKEN_PATH=calendar_token.json
```

### 5. First Run Authentication

1. Run the authentication script:
   ```bash
   python authenticate_calendar.py
   ```

2. On first run, a browser window will open for OAuth2 authentication
3. Sign in with your Google account and grant Calendar permissions
4. A `calendar_token.json` file will be created automatically
5. **Note**: This is a separate token file from Gmail's `token.json`, but uses the same `credentials.json`

## Usage

### Available Tools

1. **list_calendars** - List all calendars accessible to the user
   - Shows primary calendar and any shared calendars

2. **list_events** - List events from a calendar with optional filtering
   - Filter by time range, search query, etc.
   - Supports up to 2500 events

3. **get_event** - Get detailed information about a specific event
   - Requires event ID

4. **create_event** - Create a new calendar event
   - Supports timed events and all-day events
   - Can add attendees, location, description
   - Supports timezone settings

5. **update_event** - Update an existing calendar event
   - Can update any event property
   - Requires event ID

6. **delete_event** - Delete a calendar event
   - Requires event ID

### Event Time Formats

- **Timed events**: Use ISO 8601 format
  - Example: `2025-01-15T10:00:00` (assumes UTC)
  - Example: `2025-01-15T10:00:00-08:00` (with timezone)
  - Example: `2025-01-15T10:00:00Z` (UTC explicit)

- **All-day events**: Use date format (YYYY-MM-DD)
  - Example: `2025-01-15`
  - Set `all_day: true` when creating

### Timezone Support

Common timezone values:
- `UTC` (default)
- `America/Los_Angeles` (Pacific Time)
- `America/New_York` (Eastern Time)
- `Europe/London` (GMT/BST)
- `Asia/Tokyo` (JST)
- See [full list](https://en.wikipedia.org/wiki/List_of_tz_database_time_zones)

## Adding to Claude Desktop

Add this to your Claude Desktop config file (`%APPDATA%\Claude\claude_desktop_config.json` on Windows):

```json
{
  "mcpServers": {
    "calendar": {
      "command": "python",
      "args": [
        "C:\\Users\\visha\\Desktop\\Datathon2025\\CanvasMPC\\calendar_mcp_server.py"
      ],
      "env": {
        "CALENDAR_CREDENTIALS_PATH": "C:\\Users\\visha\\Desktop\\Datathon2025\\CanvasMPC\\credentials.json",
        "CALENDAR_TOKEN_PATH": "C:\\Users\\visha\\Desktop\\Datathon2025\\CanvasMPC\\calendar_token.json"
      }
    }
  }
}
```

**Or combine with existing servers:**

```json
{
  "mcpServers": {
    "gmail": {
      "command": "python",
      "args": ["path/to/gmail_mcp_server.py"],
      "env": {
        "GMAIL_CREDENTIALS_PATH": "path/to/credentials.json",
        "GMAIL_TOKEN_PATH": "path/to/token.json"
      }
    },
    "calendar": {
      "command": "python",
      "args": ["path/to/calendar_mcp_server.py"],
      "env": {
        "CALENDAR_CREDENTIALS_PATH": "path/to/credentials.json",
        "CALENDAR_TOKEN_PATH": "path/to/calendar_token.json"
      }
    }
  }
}
```

## Security Notes

- **Never commit `credentials.json` or `calendar_token.json` to version control**
- These files are already in `.gitignore`
- `calendar_token.json` contains your access and refresh tokens - keep it secure
- If your token is compromised, revoke access in [Google Account Security](https://myaccount.google.com/security)

## Troubleshooting

### "Calendar API not enabled" error
- Enable Calendar API in Google Cloud Console
- Go to APIs & Services > Library > Search "Calendar API" > Enable

### "Access denied" error
- Make sure your email is added as a test user in OAuth consent screen
- Same setup as Gmail API

### "Redirect URI mismatch" error
- Make sure `http://localhost:8080/` is added to authorized redirect URIs
- Same setup as Gmail API

### Token expired
- Delete `calendar_token.json` and run authentication script again
- The server will automatically refresh tokens if a refresh token is available

### Rate Limits
- Calendar API has rate limits (1,000,000 queries per day per project)
- If you hit rate limits, wait a moment and try again

## File Structure

```
.
├── calendar_mcp_server.py    # Calendar MCP server
├── authenticate_calendar.py  # Authentication script
├── credentials.json          # OAuth2 credentials (shared with Gmail)
├── calendar_token.json       # Calendar access/refresh tokens (created automatically)
├── requirements.txt          # Python dependencies
└── CALENDAR_SETUP.md        # This file
```

## Using Same Credentials for Multiple APIs

**Yes, you can use the same `credentials.json` for both Gmail and Calendar!**

Benefits:
- Single OAuth consent screen configuration
- Single set of test users
- Easier management

Just make sure:
1. Both APIs are enabled in the same Google Cloud project
2. Both scopes are requested (handled automatically by each server)
3. Test users are added to the OAuth consent screen

## Additional Resources

- [Calendar API Documentation](https://developers.google.com/calendar/api)
- [Calendar API Python Quickstart](https://developers.google.com/calendar/api/quickstart/python)
- [Calendar API Reference](https://developers.google.com/calendar/api/v3/reference)

