"""
Authentication service using Supabase for user session management.
Handles user authentication and stores per-user API tokens/credentials.
"""
import os
from typing import Optional, Dict, Any
from supabase import create_client, Client
import json

# Initialize Supabase client
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    print("Warning: SUPABASE_URL or SUPABASE_KEY not set. Auth features will be disabled.")
    supabase: Optional[Client] = None
else:
    supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)


class AuthService:
    """Service for managing user authentication and credentials."""
    
    @staticmethod
    async def get_user_credentials(user_id: str, service: str) -> Optional[Dict[str, Any]]:
        """
        Get user credentials for a specific service (canvas, google, etc.)
        
        Args:
            user_id: The user's unique identifier
            service: Service name (canvas, google_calendar, google_gmail)
        
        Returns:
            Dictionary containing credentials or None if not found
        """
        if not supabase:
            return None
        
        try:
            response = supabase.table('user_credentials') \
                .select('*') \
                .eq('user_id', user_id) \
                .eq('service', service) \
                .execute()
            
            if response.data and len(response.data) > 0:
                cred_data = response.data[0]
                # Decrypt credentials if needed
                return json.loads(cred_data['credentials'])
            return None
        except Exception as e:
            print(f"Error fetching credentials: {e}")
            return None
    
    @staticmethod
    async def store_user_credentials(
        user_id: str, 
        service: str, 
        credentials: Dict[str, Any]
    ) -> bool:
        """
        Store user credentials for a specific service.
        
        Args:
            user_id: The user's unique identifier
            service: Service name (canvas, google_calendar, google_gmail)
            credentials: Dictionary containing credentials to store
        
        Returns:
            True if successful, False otherwise
        """
        if not supabase:
            return False
        
        try:
            # Check if credentials already exist
            existing = await AuthService.get_user_credentials(user_id, service)
            
            cred_json = json.dumps(credentials)
            
            if existing:
                # Update existing credentials
                supabase.table('user_credentials') \
                    .update({'credentials': cred_json}) \
                    .eq('user_id', user_id) \
                    .eq('service', service) \
                    .execute()
            else:
                # Insert new credentials
                supabase.table('user_credentials') \
                    .insert({
                        'user_id': user_id,
                        'service': service,
                        'credentials': cred_json
                    }) \
                    .execute()
            
            return True
        except Exception as e:
            print(f"Error storing credentials: {e}")
            return False
    
    @staticmethod
    async def delete_user_credentials(user_id: str, service: str) -> bool:
        """
        Delete user credentials for a specific service.
        
        Args:
            user_id: The user's unique identifier
            service: Service name
        
        Returns:
            True if successful, False otherwise
        """
        if not supabase:
            return False
        
        try:
            supabase.table('user_credentials') \
                .delete() \
                .eq('user_id', user_id) \
                .eq('service', service) \
                .execute()
            return True
        except Exception as e:
            print(f"Error deleting credentials: {e}")
            return False
    
    @staticmethod
    async def create_session(user_id: str, session_data: Dict[str, Any]) -> Optional[str]:
        """
        Create a new user session.
        
        Args:
            user_id: The user's unique identifier
            session_data: Additional session data
        
        Returns:
            Session ID if successful, None otherwise
        """
        if not supabase:
            return None
        
        try:
            response = supabase.table('user_sessions') \
                .insert({
                    'user_id': user_id,
                    'session_data': json.dumps(session_data)
                }) \
                .execute()
            
            if response.data and len(response.data) > 0:
                return response.data[0]['id']
            return None
        except Exception as e:
            print(f"Error creating session: {e}")
            return None
    
    @staticmethod
    async def get_session(session_id: str) -> Optional[Dict[str, Any]]:
        """
        Get session data by session ID.
        
        Args:
            session_id: The session identifier
        
        Returns:
            Session data dictionary or None
        """
        if not supabase:
            return None
        
        try:
            response = supabase.table('user_sessions') \
                .select('*') \
                .eq('id', session_id) \
                .execute()
            
            if response.data and len(response.data) > 0:
                session = response.data[0]
                return {
                    'user_id': session['user_id'],
                    'session_data': json.loads(session['session_data'])
                }
            return None
        except Exception as e:
            print(f"Error fetching session: {e}")
            return None
    
    @staticmethod
    async def delete_session(session_id: str) -> bool:
        """
        Delete a user session.
        
        Args:
            session_id: The session identifier
        
        Returns:
            True if successful, False otherwise
        """
        if not supabase:
            return False
        
        try:
            supabase.table('user_sessions') \
                .delete() \
                .eq('id', session_id) \
                .execute()
            return True
        except Exception as e:
            print(f"Error deleting session: {e}")
            return False

