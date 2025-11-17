from datetime import datetime
from fastapi import APIRouter, HTTPException, status, Request

from models.index import ClientLogin, ClientSignup, SignupResponse, TokenResponse
from utils.auth import compare_password, generate_token, hash_password
from utils.file_storage import save_clients, save_conversation_states
from constants.index import available_stakeholders

router = APIRouter()

# Signup Route
@router.post("/api/signup", response_model=SignupResponse, status_code=status.HTTP_201_CREATED)
async def signup(client_info: ClientSignup, request: Request):
    """
    request:
        JSON containing user's name, email, password, position, website URL and other profile information.
        Example: {"name": "John Doe", "email": "john@example.com", "password": "SecurePass123"}
    
    response:
        JSON with signup confirmation message, client info, client ID, JWT token, and available stakeholders.
        Status code 201 for successful creation, 400 if email already exists, 500 for server errors.
        
    process:
        - Loads existing clients from application state
        - Checks if email is already registered
        - Generates unique client ID using timestamp
        - Hashes password for secure storage
        - Creates client record with metadata (creation date, etc.)
        - Initializes empty conversation state for the new client
        - Saves client data and conversation state to persistent storage
        - Generates JWT token for authentication
        - Returns success response with client data and token
    """
    try:
        print(client_info)
        clients = request.app.state.clients
        conversation_states = request.app.state.conversation_states

        existing_client = next(
            (c for c in clients if c['email'] == client_info.email), None)
        if existing_client:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )

        client_id = str(int(datetime.now().timestamp() * 1000))
        print("here3", client_info)
        password_hash = hash_password(client_info.password)

        # Get client data and convert empty strings to None
        client_data = client_info.model_dump(exclude={"password"})
        # Convert empty strings to None for optional fields
        for key in ['websiteUrl', 'position', 'company', 'socialMedia']:
            if key in client_data and client_data[key] == '':
                client_data[key] = None

        client_with_metadata = {
            **client_data,
            'clientId': client_id,
            'passwordHash': password_hash,
            'createdAt': str(datetime.now()),
            'updatedAt': str(datetime.now()),
        }

        clients.append(client_with_metadata)
        print("New client signed up:", client_with_metadata)

        conversation_states[client_id] = {
            'clientId': client_id,
            'phase': 'context_setting',
            'currentStakeholder': None,
            'stakeholdersInterviewed': [],
            'pendingStakeholders': [],
            'questionIndex': 0,
            'conversationHistory': [],
        }

        save_clients(clients)
        save_conversation_states(conversation_states)

        token = generate_token(client_with_metadata)
        print(token)

        return {
            'message': 'Signup successful',
            'clientInfo': client_with_metadata,
            'clientId': client_id,
            'token': token,
            'availableStakeholders': available_stakeholders,
        }
    except Exception as error:
        print("Signup error:", error)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error during signup: {str(error)}"
        ) from error

# Login Route
@router.post("/api/login", response_model=TokenResponse)
async def login(login_data: ClientLogin, request: Request):
    """
    request:
        JSON containing user's email and password credentials.
        Example: {"email": "user@example.com", "password": "SecurePass123"}
    
    response:
        JSON with login success message, client information (ID, name, email, position), and JWT token.
        Status code 200 for success, 401 for invalid credentials, 500 for server errors.
    
    process:
        - Loads client data from application state
        - Searches for client with matching email
        - Verifies password hash matches stored hash
        - Generates new JWT token for the authenticated session
        - Returns success response with client data and token for client-side storage
        - Returns appropriate error if credentials are invalid or account setup is incomplete
    """
    try:
        clients = request.app.state.clients
        client = next(
            (c for c in clients if c['email'] == login_data.email), None)

        if not client:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password"
            )

        if not client.get('passwordHash'):
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Account setup is incomplete"
            )

        if not compare_password(login_data.password, client['passwordHash']):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password"
            )

        token = generate_token(client)

        return {
            'message': 'Login successful',
            'clientInfo': {
                'clientId': client['clientId'],
                'name': client['name'],
                'email': client['email'],
                'position': client.get('position', None),
            },
            'token': token,
        }
    except HTTPException:
        raise
    except Exception as error:
        print("Login error:", error)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred during login"
        ) from error
