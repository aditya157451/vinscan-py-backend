import os
import datetime
import secrets
from typing import Optional, Dict, Any
import bcrypt
from dotenv import load_dotenv
from fastapi import HTTPException, status, Header
import jwt  # Replace PyJWT with jose

load_dotenv()

# Generate a secure secret key if none is provided in environment
DEFAULT_SECRET_KEY = "supersecretcode"  # Simple default for consistency


def hash_password(password):
    salt = bcrypt.gensalt()
    hashed_password = bcrypt.hashpw(password.encode('utf-8'), salt)
    return hashed_password.decode('utf-8')


def compare_password(password, hashed_password):
    return bcrypt.checkpw(password.encode('utf-8'), hashed_password.encode('utf-8'))


def generate_token(client):
    payload = {
        'clientId': client['clientId'],
        'name': client['name'],
        'email': client['email'],
        'position': client.get('position', None)
    }
    secret_key = os.getenv('JWT_SECRET_KEY', 'default_secret_key')
    return jwt.encode(payload, secret_key, algorithm='HS256')


async def get_current_user(authorization: Optional[str] = Header(None)):
    if not authorization:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Unauthorized"
        )

    try:
        # Strip the "Bearer " prefix if present
        if authorization.startswith("Bearer "):
            token = authorization[7:]  # Remove "Bearer " (7 characters)
        else:
            token = authorization

        secret_key = os.getenv('JWT_SECRET_KEY', 'default_secret_key')
        # Log first part of token for debugging
        print(f"Attempting to decode token: {token[:10]}...")
        payload = jwt.decode(token, secret_key, algorithms=['HS256'])
        print(
            f"Token decoded successfully: {payload.get('clientId', 'unknown')}")
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token expired"
        )
    except jwt.InvalidTokenError as e:
        print(f"Invalid token error: {str(e)}")  # Add detailed error logging
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token"
        )
    except Exception as e:
        print(f"Unexpected error during token validation: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Authentication error"
        )
