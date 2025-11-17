from pydantic import BaseModel, EmailStr, Field, field_validator
from typing import Optional, Dict, Any, List
import re


class PasswordMixin(BaseModel):
    password: str = Field(..., min_length=6)

    @field_validator("password")
    @classmethod
    def password_strength(cls, v):
        if not any(char.isdigit() for char in v):
            raise ValueError("Password must contain atleast one digit")
        if not any(char.isupper() for char in v):
            raise ValueError(
                "Password must contain atleast one uppercase letter")


class WebsiteUrlMixin(BaseModel):
    websiteUrl: Optional[str] = None

    @field_validator('websiteUrl')
    @classmethod
    def valid_url(cls, v):
        if v is not None:
            pattern = r'^https?:\/\/(www\.)?[-a-zA-Z0-9@:%._\+~#=]{1,256}\.[a-zA-Z0-9()]{1,6}\b([-a-zA-Z0-9()@:%_\+.~#?&//=]*)$$'
            if not re.match(pattern, v):
                raise ValueError('Invalid URL format')
        return v


class ClientBase(WebsiteUrlMixin):
    name: str = Field(..., min_length=2, max_length=100)
    email: EmailStr
    position: Optional[str] = Field(None, max_length=100)
    socialMedia: Optional[Dict[str, str]] = None
    company: Optional[str] = None


class ClientSignup(ClientBase):
    password: str = Field(..., min_length=6)


class ClientSignupRequest(BaseModel):
    name: str
    email: EmailStr
    password: str = Field(..., min_length=6)
    company: Optional[str] = None
    role: Optional[str] = None


class ClientLogin(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=6)


class ClientResponse(ClientBase):
    clientId: str
    createdAt: str
    updatedAt: str


class ClientUpdate(WebsiteUrlMixin):
    name: Optional[str] = Field(None, min_length=2, max_length=100)
    position: Optional[str] = None
    socialMedia: Optional[Dict[str, str]] = None


class TokenResponse(BaseModel):
    message: str
    clientInfo: Dict[str, Any]
    token: str


class SignupResponse(TokenResponse):
    clientId: str
    availableStakeholders: List[str]


class ChatRequest(BaseModel):
    message: str
    clientId: str


class ChatResponse(BaseModel):
    message: str


class StakeholderSelection(BaseModel):
    clientId: str
    selectedStakeholders: List[str]
    otherStakeholder: Optional[str] = None


class StakeholderResponse(BaseModel):
    message: str
    nextStakeholder: str


class ConversationState(BaseModel):
    clientId: str
    phase: str
    currentStakeholder: Optional[str] = None
    stakeholdersInterviewed: List[str] = []
    pendingStakeholders: List[str] = []
    questionIndex: int = 0
    conversationHistory: List[Dict[str, str]] = []


class ConversationStateResponse(BaseModel):
    conversationState: ConversationState
    needStakeholderSelection: bool
