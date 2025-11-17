import datetime
from fastapi import APIRouter, Depends, HTTPException, status, Request

from models.index import ClientUpdate
from utils.auth import get_current_user
from utils.file_storage import save_clients

router = APIRouter()


@router.get("/api/profile")
async def get_profile(request: Request, current_user: dict = Depends(get_current_user)):
    """
    request:
        Path parameter: Authorization token.
    response:
        JSON with the user’s profile information.
    process:
        - Search for the user by email in the JSON file.
        - Return user details if found.
    """
    try:
        clients = request.app.state.clients
        client_id = current_user['clientId']

        client = next((c for c in clients if c['clientId'] == client_id), None)

        if not client:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Client not found"
            )

        client_info = {
            'clientId': client['clientId'],
            'name': client['name'],
            'email': client['email'],
            'position': client.get('position', None),
            'websiteUrl': client.get('websiteUrl', None),
            'socialMedia': client.get('socialMedia', None),
            'createdAt': client.get('createdAt', None),
            'updatedAt': client.get('updatedAt', None),
        }

        return {'client': client_info}
    except Exception as error:
        print("Error fetching profile:", error)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while fetching profile"
        ) from error

# Route for getting the clients


@router.get("/api/clients")
async def get_clients(request: Request):
    """
    request:
        No parameters required.

    response:
        JSON array containing all client records in the system.

    process:
        - Retrieves the complete list of clients from application state
        - Returns the raw client data (should typically be admin-only in production)
    """
    return request.app.state.clients


@router.get("/api/client/{client_id}")
async def get_client(client_id: str, request: Request, current_user: dict = Depends(get_current_user)):
    """
    request:
        Path parameter: client_id to retrieve information for.
        Authentication: JWT token in Authorization header.

    response:
        JSON containing the requested client's information.
        Status code 200 for success, 404 if client not found, 500 for server errors.

    process:
        - Retrieves clients list from application state
        - Searches for client with matching client_id
        - Returns client information if found, or appropriate error response
    """
    try:
        clients = request.app.state.clients
        client = next((c for c in clients if c['clientId'] == client_id), None)

        if not client:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Client not found"
            )

        return {'client': client}
    except Exception as error:
        print("Error retrieving client:", error)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while retrieving client information"
        ) from error


@router.put("/api/client/{client_id}")
async def update_client(client_id: str, updated_info: ClientUpdate, request: Request):
    """
    request:
        Path parameter: client_id to update.
        Body: JSON with fields to update (name, position, websiteUrl, socialMedia).

    response:
        JSON with success message and updated client information.
        Status code 200 for success, 404 if client not found, 500 for server errors.

    process:
        - Retrieves clients list from application state
        - Finds the client with matching client_id
        - Updates only the fields provided in the request
        - Updates the 'updatedAt' timestamp
        - Saves changes to persistent storage
        - Returns success message with updated client information
    """
    try:
        clients = request.app.state.clients
        client_index = next((i for i, c in enumerate(
            clients) if c['clientId'] == client_id), -1)

        if client_index == -1:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Client not found"
            )

        for key, value in updated_info.dict(exclude_unset=True).items():
            clients[client_index][key] = value

        clients[client_index]['updatedAt'] = str(datetime.datetime.now())

        save_clients(clients)

        return {
            'message': 'Client information updated successfully',
            'client': clients[client_index]
        }
    except Exception as error:
        print("Error updating client:", error)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while updating client information"
        ) from error
