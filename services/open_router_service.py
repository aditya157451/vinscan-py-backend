import os
import json
from typing import List, Literal, TypedDict
import httpx

class ChatMessage(TypedDict):
    role: Literal["system", "user", "assistant"]
    content: str

class OpenRouterService:
    _instance = None

    def __init__(self):
        """Private constructor to enforce singleton pattern"""
        if OpenRouterService._instance is not None:
            raise RuntimeError("Use OpenRouterService.get_instance() instead of instantiating directly.")
        
        api_key = os.environ.get("OPENROUTER_API_KEY")
        if not api_key:
            raise ValueError("Missing OPENROUTER_API_KEY in environment variables.")

        print(f"Using API key: {api_key[:10]}...")

        self.base_url = "https://openrouter.ai/api/v1"
        self.api_key = api_key
        self.headers = {
            'Authorization': f'Bearer {api_key}',
            'HTTP-Referer': 'https://vinscan-test.com',  # Required for rankings
            'X-Title': 'VinScan App',  # Required for rankings
            'Content-Type': 'application/json'
        }

    @classmethod
    def get_instance(cls) -> 'OpenRouterService':
        """Singleton pattern implementation to get a shared instance"""
        if cls._instance is None:
            cls._instance = OpenRouterService()
        return cls._instance

    async def chat(self, messages: List[ChatMessage]) -> str:
        """Send a chat completion request to OpenRouter API"""
        try:
            print('Sending request to OpenRouter API...')
            print('Messages:', json.dumps([{
                'role': m['role'],
                'content': m['content'][:50] + '...'
            } for m in messages]))

            url = f"{self.base_url}/chat/completions"
            payload = {
                "model": "google/gemini-2.0-flash-001",
                "messages": messages,
                "max_tokens": 1500,
                "temperature": 0.7
            }

            async with httpx.AsyncClient() as client:
                response = await client.post(url, headers=self.headers, json=payload)

            # Check for HTTP error codes
            if response.status_code != 200:
                print(f"API request failed with status {response.status_code}: {response.text}")
                return f"API Error: {response.text}"

            # Ensure response is JSON before parsing
            if "application/json" not in response.headers.get("Content-Type", ""):
                return f"Unexpected response format: {response.text}"

            response_data = response.json()
            print('Received response from OpenRouter API')
            print('Response:', json.dumps(response_data, indent=2))

            # Check if response has choices
            if not response_data.get('choices') or len(response_data['choices']) == 0:
                print('No choices in response:', response_data)
                return "I'm having trouble processing your response right now. Please try again."

            # Check if first choice has content
            first_choice = response_data['choices'][0]
            if not first_choice.get('message', {}).get('content'):
                print('No content in response:', first_choice)
                return "I'm having trouble processing your response right now. Please try again."

            return first_choice['message']['content']

        except Exception as error:
            print(f'OpenRouter service error: {error}')
            import traceback
            print(f'Error traceback: {traceback.format_exc()}')

            # Handle specific error messages
            if 'model' in str(error):
                return "I apologize, but I'm having trouble connecting to the AI model. Please try again in a moment."

            return "I'm having trouble processing your response right now. Please try again."
