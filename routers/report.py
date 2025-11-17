import asyncio
from fastapi import APIRouter, Depends, HTTPException, status, Request

from services.report_service import generate_report
from utils.auth import get_current_user
from utils.report_storage import get_report_by_client_id

router = APIRouter()

# Fetching report using client id
@router.get("/api/report/{client_id}")
async def get_report(client_id: str, current_user: dict = Depends(get_current_user)):
    """
    request:
        Path parameter: client_id to fetch the report for.
        Authentication: JWT token in Authorization header.
    
    response:
        JSON with the complete report or error message and status.
        Status code 200 for success, 403 for unauthorized access, 500 for server errors.
    
    process:
        - Validates if the user is authorized to access the requested report
        - Retrieves report data from storage based on client_id
        - Returns report data or appropriate error response if no report is found
    """
    try:
        if current_user['clientId'] != client_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Unauthorized access to report"
            )

        report = await get_report_by_client_id(client_id)
        if not report:
            return {'error': 'Report not found', 'status': 'not_started'}

        return {'report': report}
    except Exception as error:
        print("Error fetching report:", error)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while fetching the report"
        ) from error

# Route for generating report using client id
@router.post("/api/report/generate/{client_id}", status_code=status.HTTP_202_ACCEPTED)
async def generate_report_route(client_id: str, request: Request, current_user: dict = Depends(get_current_user)):
    """
    request:
        Path parameter: client_id to generate the report for.
        Authentication: JWT token in Authorization header.
    
    response:
        JSON with message confirming report generation has started.
        Status code 202 for accepted, 403 for unauthorized access, 400 for invalid requests.
    
    process:
        - Validates user authorization and client_id
        - Checks if sufficient conversation history exists for report generation
        - Creates an async task to generate the report in the background
        - Returns immediate confirmation while report generation continues asynchronously
    """
    try:
        conversation_states = request.app.state.conversation_states
        clients = request.app.state.clients

        if current_user['clientId'] != client_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Unauthorized access"
            )

        if client_id not in conversation_states or not conversation_states[client_id]['conversationHistory'] or len(conversation_states[client_id]['conversationHistory']) == 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No interview data found. Please complete the interview process first."
            )

        client = next((c for c in clients if c['clientId'] == client_id), None)

        asyncio.create_task(generate_report(
            client_id, conversation_states[client_id]['conversationHistory'], client))
        print("Report generation triggered")

        return {'message': 'Report generation started', 'status': 'generating'}
    except Exception as error:
        print("Error generating report:", error)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while generating the report"
        ) from error
