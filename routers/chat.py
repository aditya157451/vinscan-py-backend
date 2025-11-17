import asyncio
import datetime
from fastapi import APIRouter, Depends, HTTPException, Request, status

from models.index import ChatRequest, ChatResponse, ConversationStateResponse, StakeholderResponse, StakeholderSelection
from services.gemini_service import generate_response
from services.report_service import generate_report
from utils.auth import get_current_user
from utils.file_storage import save_conversation_states
from constants.index import ceo_questions, stakeholder_questions

router = APIRouter()

@router.post("/api/select-stakeholders", response_model=StakeholderResponse)
async def select_stakeholders(selection: StakeholderSelection, request: Request):
    """
    request:
        Body: JSON with client ID and selected stakeholders list.
        Example: {"clientId": "123456", "selectedStakeholders": ["CEO", "Marketing Manager"]}
    
    response:
        JSON message confirming stakeholder selection and providing the next stakeholder to interview.
        Status code 201 for successful creation, 400 for validation errors, 500 for server errors.
        Example: {"message": "Stakeholders selected successfully", "nextStakeholder": "CEO"}
    
    process:
        - Loads conversation states from application state
        - Validates client ID and creates state if needed
        - Validates stakeholder selection (at least one required)
        - Updates conversation state with selected stakeholders
        - Sets current stakeholder to the first one in the list
        - Changes phase to 'internal_scan'
        - Saves updated conversation state
    """
    try:
        conversation_states = request.app.state.conversation_states
        clients = request.app.state.clients
        client_id = selection.clientId

        print("Received stakeholder selection request:", selection.dict())

        if client_id not in conversation_states:
            print(f"Invalid client ID: {client_id}")
            print("Available conversation states:",
                list(conversation_states.keys()))

            client = next(
                (c for c in clients if c['clientId'] == client_id), None)
            if client:
                print(f"Recovering conversation state for client: {client_id}")
                conversation_states[client_id] = {
                    'clientId': client_id,
                    'phase': 'context_setting',
                    'currentStakeholder': None,
                    'stakeholdersInterviewed': [],
                    'pendingStakeholders': [],
                    'questionIndex': 0,
                    'conversationHistory': [],
                }
                save_conversation_states(conversation_states)
            else:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid client ID"
                )

        if not selection.selectedStakeholders or len(selection.selectedStakeholders) == 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Please select at least one stakeholder"
            )

        state = conversation_states[client_id]

        stakeholders_list = [*selection.selectedStakeholders]

        if selection.otherStakeholder and selection.otherStakeholder.strip() != "":
            stakeholders_list.append(selection.otherStakeholder.strip())

        state['pendingStakeholders'] = stakeholders_list
        state['currentStakeholder'] = stakeholders_list[0]
        state['phase'] = 'internal_scan'

        state['conversationHistory'].append({
            'role': 'assistant',
            'content': f"Thank you for selecting the stakeholders. Let's start the interview with the {state['currentStakeholder']}.",
            'timestamp': str(datetime.datetime.now()),
        })

        save_conversation_states(conversation_states)

        return {
            'message': 'Stakeholders selected successfully',
            'nextStakeholder': state['currentStakeholder']
        }
    except HTTPException:
        raise
    except Exception as error:
        print("Stakeholder selection error:", error)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while processing your stakeholder selection"
        ) from error

# Route for getting the conversation history using client id
@router.get("/api/conversation-state/{client_id}", response_model=ConversationStateResponse)
async def get_conversation_state(client_id: str, request: Request, current_user: dict = Depends(get_current_user)):
    """
    request:
        Path parameter: client_id to fetch the conversation state for.
        Authentication: JWT token in Authorization header.
    
    response:
        JSON containing the complete conversation state and a flag indicating if stakeholder selection is needed.
        Example: {"conversationState": {...}, "needStakeholderSelection": true}
        Status code 200 for success, 401 for unauthorized access, 500 for server errors.
    
    process:
        - Authenticates the user with JWT token
        - Retrieves conversation state from application state
        - Creates default state if none exists for client ID
        - Returns conversation state with flag indicating if stakeholder selection is needed
    """
    try:
        conversation_states = request.app.state.conversation_states

        if client_id not in conversation_states:
            return {
                'conversationState': {
                    'clientId': client_id,
                    'phase': 'context_setting',
                    'currentStakeholder': None,
                    'stakeholdersInterviewed': [],
                    'pendingStakeholders': [],
                    'questionIndex': 0,
                    'conversationHistory': [],
                },
                'needStakeholderSelection': True
            }

        state = conversation_states[client_id]

        return {
            'conversationState': state,
            'needStakeholderSelection': not state['currentStakeholder']
        }
    except Exception as error:
        print("Error fetching conversation state:", error)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while fetching the conversation state"
        ) from error


@router.post("/api/chat", response_model=ChatResponse)
async def chat(chat_request: ChatRequest, request: Request):
    """
    request:
        Body: JSON with client ID and user message.
        Example: {"clientId": "123456", "message": "Our company has 50 employees."}
    
    response:
        JSON with generated AI assistant response.
        Example: {"message": "Thank you for sharing that information..."}
        Status code 200 for success, 400 for validation errors, 500 for server errors.
    
    process:
        - Loads conversation state from application state
        - Validates client ID and checks if stakeholders are selected
        - Adds user message to conversation history
        - Determines next question based on current phase, stakeholder, and question index
        - Handles stakeholder selection if current stakeholder is None
        - Tracks interview progress and manages transitions between stakeholders
        - Initiates report generation when all interviews are complete
        - Generates AI response using appropriate context and prompts
        - Saves updated conversation state
    """
    try:
        conversation_states = request.app.state.conversation_states
        clients = request.app.state.clients

        message = chat_request.message
        client_id = chat_request.clientId

        print(f'Received chat message: "{message}" from client: {client_id}')

        if client_id not in conversation_states:
            print(f"Invalid client ID: {client_id}")
            print("Available conversation states:",
                list(conversation_states.keys()))

            client = next(
                (c for c in clients if c['clientId'] == client_id), None)
            if client:
                print(f"Recovering conversation state for client: {client_id}")
                conversation_states[client_id] = {
                    'clientId': client_id,
                    'phase': 'context_setting',
                    'currentStakeholder': None,
                    'stakeholdersInterviewed': [],
                    'pendingStakeholders': [],
                    'questionIndex': 0,
                    'conversationHistory': [],
                }
                save_conversation_states(conversation_states)
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Please select stakeholders first"
                )
            else:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid client ID"
                )

        state = conversation_states[client_id]
        print(
            f"Current state: phase={state['phase']}, stakeholder={state['currentStakeholder']}, questionIndex={state['questionIndex']}")

        if len(state['pendingStakeholders']) == 0 and len(state['stakeholdersInterviewed']) == 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Please select stakeholders first"
            )

        state['conversationHistory'].append(
            {'role': 'user', 'content': message, 'timestamp': str(datetime.datetime.now())})

        next_question = None

        is_short_response = len(message.strip()) <= 3
        print(f"Is short response: {is_short_response}")

        if state['phase'] == 'context_setting':
            state['phase'] = 'internal_scan'
            next_question = ceo_questions[0]
            print(f"Next question: {next_question}")
        elif state['phase'] == 'internal_scan':
            if state['currentStakeholder'] == 'CEO':
                if is_short_response:
                    next_question = "Could you please elaborate more on your previous answer? This will help me understand your business better."
                else:
                    state['questionIndex'] += 1

                    if state['questionIndex'] < len(ceo_questions):
                        next_question = ceo_questions[state['questionIndex']]
                    else:
                        state['stakeholdersInterviewed'].append('CEO')
                        state['currentStakeholder'] = None
                        state['questionIndex'] = 0

                        next_question = "Thank you for your insights. Who would you like me to interview next? Available stakeholders are: " + \
                            ", ".join(
                                [f"{i + 1}. {s}" for i, s in enumerate(state['pendingStakeholders'])])
            elif state['currentStakeholder'] is None:
                selected_stakeholder = ""

                try:
                    stakeholder_number = int(message)
                    if 1 <= stakeholder_number <= len(state['pendingStakeholders']):
                        selected_stakeholder = state['pendingStakeholders'][stakeholder_number - 1]
                except ValueError:
                    matched_stakeholder = next((s for s in state['pendingStakeholders'] if s.lower(
                    ) == message.lower() or message.lower() in s.lower()), None)
                    if matched_stakeholder:
                        selected_stakeholder = matched_stakeholder

                if selected_stakeholder:
                    state['currentStakeholder'] = selected_stakeholder
                    state['pendingStakeholders'] = [
                        s for s in state['pendingStakeholders'] if s != selected_stakeholder]
                    next_question = stakeholder_questions[selected_stakeholder][0]
                else:
                    next_question = "Please select from the available stakeholders: " + \
                        ", ".join(
                            [f"{i + 1}. {s}" for i, s in enumerate(state['pendingStakeholders'])])
            else:
                questions = stakeholder_questions[state['currentStakeholder']]

                if is_short_response:
                    next_question = "Could you please elaborate more on your previous answer? This will help me understand your business better."
                else:
                    state['questionIndex'] += 1

                    if state['questionIndex'] < len(questions):
                        next_question = questions[state['questionIndex']]
                    else:
                        state['stakeholdersInterviewed'].append(
                            state['currentStakeholder'])
                        state['currentStakeholder'] = None
                        state['questionIndex'] = 0

                        if len(state['pendingStakeholders']) > 0:
                            next_question = "Thank you for your insights. Who would you like me to interview next? Available stakeholders are: " + \
                                ", ".join(
                                    [f"{i + 1}. {s}" for i, s in enumerate(state['pendingStakeholders'])])
                        else:
                            state['phase'] = 'report_generation'
                            next_question = "Thank you for completing all the stakeholder interviews! Your VinScan report is now being generated. " + \
                                            "Please visit your dashboard to view your report once it's ready. " + \
                                            "This may take a few minutes as our AI analyzes your business information."

                            client = next(
                                (c for c in clients if c['clientId'] == client_id), None)

                            asyncio.create_task(generate_report(
                                client_id, state['conversationHistory'], client))
                            print("Report generation triggered")

        elif state['phase'] == 'market_scan':
            market_scan_questions = [
                "Could you tell me about your industry size and growth rate?",
                "What are the key trends in your industry (technological shifts, regulatory changes, consumer behavior)?",
                "What is the regulatory landscape like in your industry?",
            ]

            if is_short_response:
                next_question = "Could you please elaborate more on your previous answer? This will help me understand your market better."
            else:
                state['questionIndex'] += 1

                if state['questionIndex'] < len(market_scan_questions):
                    next_question = market_scan_questions[state['questionIndex']]
                else:
                    state['phase'] = 'competitor_scan'
                    state['questionIndex'] = 0
                    next_question = "Thank you for completing the Market Scan. Let's move on to the Competitor Scan phase. Who are your direct competitors (companies offering similar products/services to the same target market)?"

        elif state['phase'] == 'competitor_scan':
            competitor_scan_questions = [
                "Who are your direct competitors (companies offering similar products/services to the same target market)?",
            ]

            if is_short_response:
                next_question = "Could you please elaborate more on your previous answer? This will help me understand your competitors better."
            else:
                state['questionIndex'] += 1

                if state['questionIndex'] < len(competitor_scan_questions):
                    next_question = competitor_scan_questions[state['questionIndex']]
                else:
                    next_question = "Thank you for completing the Competitor Scan. We have now gathered all the necessary information for your VinScan report. Our team will analyze this information and provide you with a comprehensive report soon. Is there anything else you'd like to add or discuss?"

        response = "I'm having trouble processing your response right now. Could you please try again or provide more details?"

        try:
            client = next(
                (c for c in clients if c['clientId'] == client_id), None)
            response = await generate_response(message, [{'role': msg['role'], 'content': msg['content']} for msg in state['conversationHistory']], state['phase'], state['currentStakeholder'], next_question, client)
            print(
                f"Generating response with AI: phase={state['phase']}, stakeholder={state['currentStakeholder']}, nextQuestion={next_question}")
            print(f"AI response: \"{response[:50]}...\"")

            state['conversationHistory'].append(
                {'role': 'assistant', 'content': response, 'timestamp': str(datetime.datetime.now())})

            save_conversation_states(conversation_states)

            return {'message': response}
        except Exception as error:
            print("Error generating response:", error)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to generate response"
            ) from error
    except HTTPException:
        raise
    except Exception as error:
        print("Chat error:", error)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while processing your message"
        ) from error
