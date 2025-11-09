# Canvas MCP Frontend

A Streamlit-based frontend for interacting with Canvas, Google Calendar, and Gmail through Claude via OpenRouter.

## Quick Start

1. **Install dependencies:**
```bash
pip install -r requirements.txt
```

2. **Set up environment variables:**
   - Copy `env.example` to `.env`
   - Add your `OPENROUTER_API_KEY`
   - Add your `CANVAS_API_KEY` (if using Canvas features)
   - Ensure Google Calendar and Gmail credentials are set up (see CALENDAR_SETUP.md and GMAIL_SETUP.md)

3. **Start the backend:**
```bash
uvicorn backend.api:app --reload --port 8000
```

4. **Start the frontend:**
```bash
streamlit run frontend.py
```

5. **Open your browser:**
   - Navigate to `http://localhost:8501`
   - Start chatting with the assistant!

## Features

- **Canvas Integration**: View courses, assignments, create assignments, and more
- **Calendar Integration**: List events, create events, manage your calendar
- **Gmail Integration**: Read emails, send emails, search your inbox

## Example Queries

- "What courses do I have?"
- "Show me assignments due in the next week"
- "What events do I have tomorrow?"
- "Send an email to example@email.com with subject 'Hello'"
- "Create a calendar event for tomorrow at 2pm called 'Meeting'"

## Architecture

- **Frontend**: Streamlit web interface (`frontend.py`)
- **Backend**: FastAPI server (`backend/api.py`)
- **Service Layer**: Wraps MCP server functions (`backend/service_layer.py`)
- **MCP Servers**: Canvas, Calendar, and Gmail integrations

For more details, see `FRONTEND_SETUP.md`.

