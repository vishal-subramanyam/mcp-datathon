# Frontend Setup Guide

## Overview
This guide explains how to set up and run the Streamlit frontend and FastAPI backend for the Canvas MCP system.

## Prerequisites
1. Python 3.8 or higher
2. OpenRouter API key
3. Canvas API key
4. Google Calendar and Gmail credentials (if using those features)

## Installation

1. **Install dependencies:**
```bash
pip install -r requirements.txt
```

2. **Set up environment variables:**
   - Copy `env.example` to `.env` (or set environment variables directly)
   - Fill in your API keys and credentials paths

3. **Ensure MCP server credentials are set up:**
   - Canvas: Set `CANVAS_API_KEY` in `.env`
   - Calendar: Have `calendar_token.json` and `credentials.json` ready
   - Gmail: Have `token.json` and `credentials.json` ready

## Running the Application

### Option 1: Run Backend and Frontend Separately

1. **Start the FastAPI backend:**
   
   From the root directory (recommended):
   ```bash
   uvicorn backend.api:app --reload --port 8000 --host 127.0.0.1
   ```
   
   Or if you're in the backend directory:
   ```bash
   cd backend
   uvicorn api:app --reload --port 8000 --host 127.0.0.1
   ```
   
   **Note:** Using `--host 127.0.0.1` explicitly helps avoid Windows proxy/firewall issues with `localhost`.
   
   You should see output like:
   ```
   INFO:     Uvicorn running on http://127.0.0.1:8000 (Press CTRL+C to quit)
   INFO:     Started reloader process
   INFO:     Started server process
   INFO:     Waiting for application startup.
   INFO:     Application startup complete.
   ```

2. **Start the Streamlit frontend:**
```bash
streamlit run frontend.py
```

### Option 2: Use a Process Manager

You can use `pm2`, `supervisord`, or similar tools to run both processes.

## Usage

1. Open your browser and navigate to the Streamlit app (usually `http://localhost:8501`)
2. Type your query in the chat input
3. The assistant will use the appropriate MCP tools to answer your query

## Example Queries

- "What courses do I have?"
- "Show me assignments due in the next week"
- "What events do I have tomorrow?"
- "Send an email to john@example.com with subject 'Hello' and body 'Hi there'"
- "Create a calendar event for tomorrow at 2pm called 'Team Meeting'"

## Troubleshooting

1. **Backend not responding / Connection errors:**
   - **Verify backend is running**: Check the terminal where you started uvicorn - you should see "Application startup complete"
   - **Test in browser**: Try opening `http://127.0.0.1:8000/health` in your browser - you should see `{"status":"healthy",...}`
   - **Check port**: Make sure port 8000 is not being used by another application
   - **Windows Firewall**: Windows Firewall might block localhost connections. Try:
     - Running as administrator
     - Adding Python to Windows Firewall exceptions
     - Temporarily disabling firewall to test
   - **Proxy issues**: If you're on a corporate network with a proxy:
     - Try disabling proxy for localhost/127.0.0.1
     - Use `127.0.0.1` instead of `localhost` (already configured)
   - **Verify OpenRouter API key**: Make sure `OPENROUTER_API_KEY` is set in your `.env` file
   - **Check backend logs**: Look for error messages in the terminal where uvicorn is running

2. **Tool calls failing:**
   - Ensure all API keys and credentials are set up correctly
   - Check that the MCP server helper functions can be imported
   - Verify that Canvas/Calendar/Gmail API credentials are valid

3. **CORS errors:**
   - The backend is configured to allow all origins in development
   - In production, update the CORS settings in `backend/api.py`

4. **Import errors:**
   - Make sure you're running from the project root directory
   - Verify that all MCP server files are in the root directory
   - Check that `backend/service_layer.py` can import the MCP server modules

## Architecture

The system consists of:
1. **Frontend (Streamlit)**: User interface for chatting with the assistant
2. **Backend (FastAPI)**: API server that handles queries and integrates with OpenRouter
3. **Service Layer**: Wraps MCP server functions for programmatic access
4. **MCP Servers**: Canvas, Calendar, and Gmail integration servers

## API Endpoints

- `POST /chat`: Process a user query and return a response
- `GET /health`: Health check endpoint
- `GET /tools`: Get all available tools

## Configuration

The backend uses the following environment variables:
- `OPENROUTER_API_KEY`: Your OpenRouter API key (required)
- `CANVAS_API_KEY`: Your Canvas API key (required for Canvas features)
- `CALENDAR_TOKEN_PATH`: Path to calendar token file
- `CALENDAR_CREDENTIALS_PATH`: Path to calendar credentials file
- `GMAIL_TOKEN_PATH`: Path to Gmail token file
- `GMAIL_CREDENTIALS_PATH`: Path to Gmail credentials file

