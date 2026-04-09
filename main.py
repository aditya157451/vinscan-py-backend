from datetime import datetime
import os
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from contextlib import asynccontextmanager

from routers.auth import router as auth_router
from routers.users import router as users_router
from routers.chat import router as chat_router
from routers.report import router as report_router

from utils.file_storage import load_clients, load_conversation_states, save_clients, save_conversation_states

load_dotenv()

CLIENTS_FILE = "data/clients.json"
CONVERSATION_STATES_FILE = "data/conversation_states.json"

# Application startup and shutdown events


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Load data on startup
    app.state.clients = load_clients()
    app.state.conversation_states = load_conversation_states()
    print("Data loaded from storage files")
    yield
    # Save data on shutdown
    save_clients(app.state.clients)
    save_conversation_states(app.state.conversation_states)
    print("Data saved to storage files")

# Initialize FastAPI app
app = FastAPI(title="AI Business Interview & Reporting System", lifespan=lifespan)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Routes


@app.get("/")
async def root():
    return FileResponse("static/index.html")

@app.get("/dashboard")
async def dashboard():
    return FileResponse("static/dashboard.html")

@app.get("/chat")
async def chat():
    return FileResponse("static/chat.html")

@app.get("/report")
async def report():
    return FileResponse("static/report.html")

app.include_router(auth_router)

app.include_router(users_router)

app.include_router(chat_router)

app.include_router(report_router)

if __name__ == '__main__':
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=int(os.environ.get('PORT', 5003)))
