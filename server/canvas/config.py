"""Canvas API configuration."""

import os
from zoneinfo import ZoneInfo
from datetime import timezone as dt_timezone

# Canvas API URL
API_URL = os.getenv("CANVAS_API_URL", "https://canvas.instructure.com")

# Canvas API Key (loaded from environment)
def get_api_key() -> str:
    """Get Canvas API key from environment."""
    API_KEY = os.getenv("CANVAS_API_KEY")
    
    # If not found, try loading from .env file
    if not API_KEY:
        try:
            from dotenv import load_dotenv
            load_dotenv()
            API_KEY = os.getenv("CANVAS_API_KEY")
        except ImportError:
            pass
    
    if not API_KEY:
        raise ValueError(
            "CANVAS_API_KEY not found. Please set it as an environment variable or in a .env file."
        )
    
    if not API_KEY.strip():
        raise ValueError("CANVAS_API_KEY is set but empty. Please provide a valid API key.")
    
    return API_KEY.strip()

# Timezone configuration
def get_timezone():
    """Get the user's timezone from environment or default to Chicago timezone."""
    tz_str = os.getenv("CANVAS_TIMEZONE")
    
    if not tz_str:
        try:
            from dotenv import load_dotenv
            load_dotenv()
            tz_str = os.getenv("CANVAS_TIMEZONE")
        except ImportError:
            pass
    
    if tz_str:
        try:
            return ZoneInfo(tz_str)
        except Exception:
            # Fall back to default if invalid
            pass
    
    # Default to Chicago timezone
    return ZoneInfo("America/Chicago")

# Get the configured timezone
USER_TIMEZONE = get_timezone()

