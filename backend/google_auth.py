"""
Google OAuth 2.0 implementation for VT Calendar
Handles authentication and token management for Google Calendar API
"""
import os
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
import json
from datetime import datetime, timedelta
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Google OAuth2 configuration
GOOGLE_CLIENT_ID = os.getenv('GOOGLE_CLIENT_ID')
GOOGLE_CLIENT_SECRET = os.getenv('GOOGLE_CLIENT_SECRET')
REDIRECT_URI = os.getenv('GOOGLE_REDIRECT_URI', 'http://localhost:3001/api/auth/google/callback')
SCOPES = ['https://www.googleapis.com/auth/calendar.events', 'https://www.googleapis.com/auth/calendar.readonly']

if not GOOGLE_CLIENT_ID or not GOOGLE_CLIENT_SECRET:
    raise ValueError("GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET must be set in environment variables")

def get_google_auth_url():
    """Generate the Google OAuth2 authorization URL"""
    flow = Flow.from_client_config(
        {"web": {
            "client_id": GOOGLE_CLIENT_ID,
            "client_secret": GOOGLE_CLIENT_SECRET,
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token"
        }},
        scopes=SCOPES,
        redirect_uri=REDIRECT_URI
    )
    
    auth_url, _ = flow.authorization_url(
        access_type='offline',
        prompt='consent',
        include_granted_scopes='true'
    )
    
    return auth_url

def get_google_tokens(authorization_response):
    """Exchange authorization code for tokens"""
    flow = Flow.from_client_config(
        {"web": {
            "client_id": GOOGLE_CLIENT_ID,
            "client_secret": GOOGLE_CLIENT_SECRET,
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token"
        }},
        scopes=SCOPES,
        redirect_uri=REDIRECT_URI
    )
    
    flow.fetch_token(authorization_response=authorization_response)
    
    return {
        'token': flow.credentials.token,
        'refresh_token': flow.credentials.refresh_token,
        'token_uri': flow.credentials.token_uri,
        'client_id': GOOGLE_CLIENT_ID,
        'client_secret': GOOGLE_CLIENT_SECRET,
        'scopes': flow.credentials.scopes,
        'expiry': flow.credentials.expiry.isoformat() if flow.credentials.expiry else None
    }

def get_google_calendar_service(tokens):
    """Get Google Calendar service using stored tokens"""
    creds = Credentials(
        token=tokens['token'],
        refresh_token=tokens['refresh_token'],
        token_uri=tokens['token_uri'],
        client_id=tokens['client_id'],
        client_secret=tokens['client_secret'],
        scopes=tokens['scopes']
    )
    
    if tokens['expiry']:
        creds.expiry = datetime.fromisoformat(tokens['expiry'])
    
    # Refresh token if expired
    if creds.expired and creds.refresh_token:
        creds.refresh(Request())
    
    return build('calendar', 'v3', credentials=creds)
