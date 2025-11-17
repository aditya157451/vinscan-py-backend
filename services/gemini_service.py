from pydantic import BaseModel
from typing import List, Optional
import os
from dotenv import load_dotenv
import httpx

from .open_router_service import OpenRouterService
from constants.prompts import assistant_system_prompt, phase_prompts, stakeholder_prompts

# Load environment variables
load_dotenv()

# Define request model
class ConversationMessage(BaseModel):
    role: str
    content: str

class GenerateResponseRequest(BaseModel):
    userMessage: str
    conversationHistory: List[ConversationMessage]
    phase: str
    currentStakeholder: Optional[str] = None
    nextQuestion: Optional[str] = None
    clientInfo: Optional[dict] = None


# OpenRouter API settings
OPENROUTER_API_KEY = os.getenv('OPENROUTER_API_KEY')
OPENROUTER_API_URL = "https://openrouter.ai/api/v1/chat/completions"


def build_system_prompt(phase: str, currentStakeholder: Optional[str], clientInfo: Optional[dict]) -> str:

    if clientInfo:
        client_context = (
            f"You are speaking with {clientInfo.get('name')}, who is the {clientInfo.get('position')} at {clientInfo.get('websiteUrl', 'their organization')}.\n"
            f"Their email is {clientInfo.get('email')} and their LinkedIn profile is {clientInfo.get('socialMedia', 'not provided')}.\n"
            "Please address them by name occasionally to personalize the conversation."
        )
        system_prompt = assistant_system_prompt
        system_prompt = client_context + "\n\n" + system_prompt

    if phase in phase_prompts:
        system_prompt += "\n\n" + phase_prompts[phase]

    if currentStakeholder and currentStakeholder in stakeholder_prompts:
        system_prompt += "\n\n" + stakeholder_prompts[currentStakeholder]

    return system_prompt

# async def call_openrouter_api(messages: List[dict]) -> str:
#     try:
#         headers = {
#             "Authorization": f"Bearer {OPENROUTER_API_KEY}",
#             "Content-Type": "application/json",
#             "HTTP-Referer": "https://vinscan-test.com",  # Replace with your actual domain
#             "X-Title": "VinScan"  # Your app name
#         }

#         payload = {
#             "model": "google/gemini-2.0-flash-001",
#             "messages": messages,
#             "max_tokens": 1000
#         }

#         async with httpx.AsyncClient(timeout=60.0) as client:
#             response = await client.post(
#                 OPENROUTER_API_URL,
#                 headers=headers,
#                 json=payload
#             )

#             if response.status_code != 200:
#                 print(f"Error from OpenRouter API: {response.status_code} - {response.text}")
#                 return "I'm having trouble processing your response right now. Could you please try again or provide more details?"

#             response_data = response.json()

#             if not response_data.get("choices") or len(response_data["choices"]) == 0:
#                 print("No choices in response:", response_data)
#                 return "I'm having trouble processing your response right now. Could you please try again or provide more details?"

#             return response_data["choices"][0]["message"]["content"]
#     except Exception as error:
#         print("Error generating response with OpenRouter:", error)
#         return "I'm having trouble processing your response right now. Could you please try again or provide more details?"


async def generate_response(user_message: str, conversation_history: List[dict], phase: str, current_stakeholder: Optional[str] = None, next_question: Optional[str] = None, client_info: Optional[dict] = None):
    try:
        open_router = OpenRouterService.get_instance()
        request_data = GenerateResponseRequest(
            userMessage=user_message,
            conversationHistory=[ConversationMessage(
                role=msg['role'], content=msg['content']) for msg in conversation_history],
            phase=phase,
            currentStakeholder=current_stakeholder,
            nextQuestion=next_question,
            clientInfo=client_info
        )

        system_prompt = build_system_prompt(
            request_data.phase, request_data.currentStakeholder, request_data.clientInfo)

        messages = [{"role": "system", "content": system_prompt}]
        messages.extend([{"role": msg.role, "content": msg.content}
                        for msg in request_data.conversationHistory])

        if request_data.nextQuestion:
            messages.append(
                {"role": "system", "content": f"After acknowledging the user's response, ask: '{request_data.nextQuestion}'."})

        response = await open_router.chat(messages)
        return response
    except Exception as error:
        print("Error in generate_response function:", error)
        return "I'm having trouble processing your response right now. Could you please try again or provide more details?"
