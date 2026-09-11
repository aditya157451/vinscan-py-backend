# VinScan Python Backend

VinScan is a FastAPI backend for an AI business interview and reporting system. It serves a small static web interface, manages client signup/login, guides users through stakeholder interviews, stores conversation state in JSON files, and generates business reports with OpenRouter.

## Features

- Client signup and login with hashed passwords
- JWT-based authentication for protected profile and report endpoints
- Static pages for landing, dashboard, chat, and report views
- Stakeholder interview flow with conversation state tracking
- AI-generated chat responses through OpenRouter
- Background report generation with market scan, competitor analysis, SWOT analysis, and strategic recommendations
- Local JSON persistence for clients, conversation states, and reports

## Tech Stack

- Python
- FastAPI
- Uvicorn
- Pydantic
- PyJWT
- bcrypt
- httpx
- OpenRouter API

## Project Structure

```text
.
|-- main.py                  # FastAPI app entry point
|-- requirements.txt         # Python dependencies
|-- constants/               # Stakeholders, interview questions, and prompts
|-- models/                  # Pydantic request/response schemas
|-- routers/                 # API route modules
|-- services/                # AI chat and report generation services
|-- static/                  # HTML, CSS, and JavaScript frontend files
|-- utils/                   # Auth, file storage, and report storage helpers
`-- data/                    # Runtime JSON storage, created automatically
```

## How Files Connect When The Project Runs

The project starts from `main.py`. When you run `uvicorn main:app --reload`, Uvicorn imports the `app` object from `main.py`, loads environment variables, creates the FastAPI application, mounts the static frontend, loads JSON data into memory, and connects all API routers.

```text
uvicorn main:app
    |
    `-- main.py
        |-- loads .env
        |-- creates FastAPI app
        |-- mounts /static files
        |-- serves HTML pages
        |-- loads data from utils/file_storage.py
        |-- includes routers/auth.py
        |-- includes routers/users.py
        |-- includes routers/chat.py
        `-- includes routers/report.py
```

### Runtime Connection Map

```text
Browser
    |
    |-- /                 -> static/index.html
    |-- /dashboard        -> static/dashboard.html
    |-- /chat             -> static/chat.html
    `-- /report           -> static/report.html

Static HTML pages
    |
    |-- static/css/*.css   -> page styling
    `-- static/js/*.js     -> browser behavior and API calls

Frontend JavaScript
    |
    |-- static/js/api.js    -> central fetch client for all /api routes
    |-- static/js/auth.js   -> login, signup, logout, localStorage auth state
    |-- static/js/chat.js   -> stakeholder selection and interview messages
    |-- static/js/report.js -> report loading, polling, export, print
    `-- static/js/utils.js  -> shared UI helpers, validation, formatting

API Routers
    |
    |-- routers/auth.py     -> /api/signup and /api/login
    |-- routers/users.py    -> profile and client endpoints
    |-- routers/chat.py     -> stakeholder selection and interview chat
    `-- routers/report.py   -> report fetch and report generation

Shared Backend Modules
    |
    |-- models/index.py              -> Pydantic schemas for request/response validation
    |-- utils/auth.py                -> password hashing, JWT creation, JWT validation
    |-- utils/file_storage.py        -> clients and conversation JSON storage
    |-- utils/report_storage.py      -> report JSON storage
    |-- constants/index.py           -> stakeholders and fixed interview questions
    |-- constants/prompts.py         -> AI prompts used by chat/report services
    |-- services/gemini_service.py   -> builds chat prompt and calls OpenRouter service
    |-- services/report_service.py   -> creates report sections in the background
    `-- services/open_router_service.py -> sends requests to OpenRouter API

Runtime Data
    |
    |-- data/clients.json
    |-- data/conversation_states.json
    `-- data/reports.json
```

## Startup Flow

1. `uvicorn main:app --reload --host 0.0.0.0 --port 8000` starts the server.
2. `main.py` calls `load_dotenv()` so values from `.env` are available.
3. `main.py` imports routers from the `routers/` folder.
4. `main.py` imports storage helpers from `utils/file_storage.py`.
5. `utils/file_storage.py` makes sure the `data/` directory and JSON files exist.
6. FastAPI runs the `lifespan()` function in `main.py`.
7. `lifespan()` loads clients and conversation states into `app.state`.
8. `main.py` mounts the `static/` folder at `/static`.
9. `main.py` registers page routes like `/`, `/dashboard`, `/chat`, and `/report`.
10. `main.py` includes the API routers so all `/api/...` endpoints become active.

When the app shuts down, `lifespan()` saves `app.state.clients` and `app.state.conversation_states` back into JSON files.

## Frontend To Backend Flow

The frontend is plain HTML, CSS, and JavaScript. The HTML files render pages, and the JavaScript files call the backend API.

```text
User clicks or submits a form
    |
    `-- page-specific JS handles the event
        |
        `-- static/js/api.js sends fetch request
            |
            `-- FastAPI router receives /api request
                |
                |-- models/index.py validates request body
                |-- utils/auth.py checks JWT if endpoint is protected
                |-- services/* runs AI/report logic when needed
                `-- utils/* reads or writes JSON data
```

### Signup Flow

```text
static/index.html
    |
    `-- static/js/auth.js
        |
        `-- api.signup() in static/js/api.js
            |
            `-- POST /api/signup in routers/auth.py
                |
                |-- ClientSignup schema from models/index.py validates input
                |-- hash_password() from utils/auth.py hashes password
                |-- available_stakeholders from constants/index.py is returned
                |-- save_clients() writes data/clients.json
                |-- save_conversation_states() writes data/conversation_states.json
                `-- generate_token() from utils/auth.py returns JWT
```

The browser stores the returned token, client ID, client info, and available stakeholders in `localStorage`.

### Login Flow

```text
static/index.html
    |
    `-- static/js/auth.js
        |
        `-- api.login() in static/js/api.js
            |
            `-- POST /api/login in routers/auth.py
                |
                |-- ClientLogin schema from models/index.py validates input
                |-- compare_password() from utils/auth.py checks password
                `-- generate_token() from utils/auth.py returns JWT
```

After login, the browser redirects the user to `/dashboard`.

### Chat And Interview Flow

```text
static/chat.html
    |
    `-- static/js/chat.js
        |
        |-- api.getConversationState()
        |       `-- GET /api/conversation-state/{client_id}
        |
        |-- api.selectStakeholders()
        |       `-- POST /api/select-stakeholders
        |
        `-- api.sendMessage()
                `-- POST /api/chat
```

On the backend:

```text
routers/chat.py
    |
    |-- reads app.state.conversation_states
    |-- uses constants/index.py for interview questions
    |-- saves user messages into conversation history
    |-- decides the next question and interview phase
    |-- calls generate_response() from services/gemini_service.py
    |       |
    |       |-- builds system prompt from constants/prompts.py
    |       `-- calls OpenRouterService.chat()
    |              |
    |              `-- services/open_router_service.py sends request to OpenRouter
    |
    `-- save_conversation_states() persists updates to data/conversation_states.json
```

When all selected stakeholder interviews are complete, `routers/chat.py` starts report generation in the background by calling `generate_report()` from `services/report_service.py`.

### Report Flow

```text
static/report.html
    |
    `-- static/js/report.js
        |
        |-- api.getReport()
        |       `-- GET /api/report/{client_id}
        |
        `-- api.generateReport()
                `-- POST /api/report/generate/{client_id}
```

On the backend:

```text
routers/report.py
    |
    |-- get_current_user() from utils/auth.py validates JWT
    |-- get_report_by_client_id() reads data/reports.json
    `-- generate_report() starts background report generation
```

`services/report_service.py` creates the report:

```text
services/report_service.py
    |
    |-- saves initial status: generating
    |-- calls OpenRouter for Market Scan
    |-- calls OpenRouter for Competitor Analysis
    |-- calls OpenRouter for SWOT Analysis
    |-- calls OpenRouter for Strategic Recommendations
    |-- calls OpenRouter for Executive Summary
    `-- save_report_to_database() writes final report to data/reports.json
```

While the report status is `generating`, `static/js/report.js` polls the backend every few seconds until the report becomes `completed` or `failed`.

## Backend Module Responsibilities

| File | Purpose | Used By |
| --- | --- | --- |
| `main.py` | Creates FastAPI app, page routes, static mounting, CORS, lifespan loading/saving | Uvicorn |
| `routers/auth.py` | Signup and login endpoints | `main.py`, frontend auth calls |
| `routers/users.py` | Profile and client CRUD-style endpoints | `main.py`, frontend profile calls |
| `routers/chat.py` | Stakeholder selection, conversation state, AI interview chat | `main.py`, chat page |
| `routers/report.py` | Report fetch and report generation endpoints | `main.py`, report page |
| `models/index.py` | Request and response validation schemas | All routers |
| `utils/auth.py` | Password hashing, token creation, token verification | Auth, users, chat, report routers |
| `utils/file_storage.py` | Creates, loads, and saves clients/conversation JSON files | `main.py`, auth/chat/users routers |
| `utils/report_storage.py` | Creates, reads, and saves reports JSON file | Report router and report service |
| `services/open_router_service.py` | Low-level OpenRouter chat-completion API client | AI services |
| `services/gemini_service.py` | Builds interview AI prompt and generates chat reply | Chat router |
| `services/report_service.py` | Generates report sections and summary | Chat and report routers |
| `constants/index.py` | Stakeholder list and interview question sets | Auth and chat routers |
| `constants/prompts.py` | System, phase, and stakeholder prompts | AI services |

## Frontend Module Responsibilities

| File | Purpose | Talks To |
| --- | --- | --- |
| `static/index.html` | Login/signup landing page | `auth.js`, `api.js` |
| `static/dashboard.html` | Authenticated dashboard page | `auth.js`, `api.js` |
| `static/chat.html` | Stakeholder interview chat UI | `chat.js`, `api.js` |
| `static/report.html` | Report display and export UI | `report.js`, `api.js` |
| `static/js/api.js` | Central API client and local token handling | All `/api/...` endpoints |
| `static/js/auth.js` | Login, signup, logout, auth redirects | `/api/signup`, `/api/login` |
| `static/js/chat.js` | Loads conversation state and sends chat messages | Chat endpoints |
| `static/js/report.js` | Loads reports, starts generation, polls status | Report endpoints |
| `static/js/utils.js` | Toasts, validation, formatting, loading states | Other frontend JS files |
| `static/css/*.css` | Visual styling and responsive layout | HTML pages |

## Requirements

- Python 3.10 or newer
- An OpenRouter API key

## Setup

1. Create and activate a virtual environment:

```bash
python -m venv .venv
.venv\Scripts\activate
```

On macOS/Linux:

```bash
python -m venv .venv
source .venv/bin/activate
```

2. Install dependencies:

```bash
pip install -r requirements.txt
```

3. Create a `.env` file in the project root:

```env
OPENROUTER_API_KEY=your_openrouter_api_key
JWT_SECRET_KEY=replace_with_a_strong_secret
PORT=8000
```

`OPENROUTER_API_KEY` is required for AI chat and report generation. `JWT_SECRET_KEY` is used to sign and verify authentication tokens. `PORT` is optional and defaults to `8000`.

## Run Locally

```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

Then open:

- `http://localhost:8000/` for the landing page
- `http://localhost:8000/dashboard` for the dashboard
- `http://localhost:8000/chat` for the interview chat
- `http://localhost:8000/report` for generated reports
- `http://localhost:8000/docs` for the FastAPI Swagger UI

You can also run the app directly:

```bash
python main.py
```

## API Overview

### Auth

| Method | Endpoint | Description |
| --- | --- | --- |
| `POST` | `/api/signup` | Create a client account and return a JWT token |
| `POST` | `/api/login` | Authenticate a client and return a JWT token |

### Users

| Method | Endpoint | Description |
| --- | --- | --- |
| `GET` | `/api/profile` | Get the authenticated client's profile |
| `GET` | `/api/clients` | Get all clients |
| `GET` | `/api/client/{client_id}` | Get one client by ID |
| `PUT` | `/api/client/{client_id}` | Update client profile fields |

### Chat and Interview Flow

| Method | Endpoint | Description |
| --- | --- | --- |
| `POST` | `/api/select-stakeholders` | Select stakeholders for the interview flow |
| `GET` | `/api/conversation-state/{client_id}` | Fetch saved interview state |
| `POST` | `/api/chat` | Send a user message and receive an AI response |

### Reports

| Method | Endpoint | Description |
| --- | --- | --- |
| `GET` | `/api/report/{client_id}` | Fetch a generated report |
| `POST` | `/api/report/generate/{client_id}` | Start report generation in the background |

Protected endpoints expect an authorization header:

```http
Authorization: Bearer <token>
```

## Example Requests

### Signup

```bash
curl -X POST http://localhost:8000/api/signup ^
  -H "Content-Type: application/json" ^
  -d "{\"name\":\"Jane Doe\",\"email\":\"jane@example.com\",\"password\":\"Secure123\",\"position\":\"Founder\",\"company\":\"Example Co\",\"websiteUrl\":\"https://example.com\"}"
```

### Login

```bash
curl -X POST http://localhost:8000/api/login ^
  -H "Content-Type: application/json" ^
  -d "{\"email\":\"jane@example.com\",\"password\":\"Secure123\"}"
```

### Select Stakeholders

```bash
curl -X POST http://localhost:8000/api/select-stakeholders ^
  -H "Content-Type: application/json" ^
  -d "{\"clientId\":\"CLIENT_ID\",\"selectedStakeholders\":[\"CEO\",\"Marketing Head\"]}"
```

### Chat

```bash
curl -X POST http://localhost:8000/api/chat ^
  -H "Content-Type: application/json" ^
  -d "{\"clientId\":\"CLIENT_ID\",\"message\":\"We serve mid-market manufacturing companies.\"}"
```

## Data Storage

The application stores runtime data in JSON files under `data/`. This directory is created automatically when the storage helpers are imported.

- `data/clients.json` stores registered clients
- `data/conversation_states.json` stores interview progress
- `data/reports.json` stores generated report data

This is useful for local development and demos. For production, replace JSON file storage with a database and tighten access control around client and admin endpoints.

## Notes

- Report generation runs asynchronously after interviews are completed or when `/api/report/generate/{client_id}` is called.
- AI features require a valid `OPENROUTER_API_KEY`.
- The current OpenRouter model is configured as `google/gemini-2.0-flash-001` in `services/open_router_service.py`.
- CORS is currently open to all origins for development convenience.
