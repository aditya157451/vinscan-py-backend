import json
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "../data")
CLIENTS_FILE = os.path.join(DATA_DIR, "clients.json")
REPORTS_FILE = os.path.join(DATA_DIR, "reports.json")
CONVERSATION_STATES_FILE = os.path.join(DATA_DIR, "conversation_states.json")

# Ensure data directory exists
os.makedirs(DATA_DIR, exist_ok=True)

# Ensure clients file exists
if not os.path.exists(CLIENTS_FILE):
    with open(CLIENTS_FILE, "w") as f:
        json.dump([], f, indent=2)

# Ensure reports file exists
if not os.path.exists(REPORTS_FILE):
    with open(REPORTS_FILE, "w") as f:
        json.dump({}, f, indent=2)

# Ensure conversation file exists
if not os.path.exists(CONVERSATION_STATES_FILE):
    with open(CONVERSATION_STATES_FILE, "w") as f:
        json.dump({}, f, indent=2)


def load_clients():
    try:
        with open(CLIENTS_FILE, "r") as f:
            data = json.load(f)
            # Ensure we always return a list, even if file contains a dict
            if isinstance(data, dict):
                # Convert dict to list (legacy format)
                return list(data.values()) if data else []
            return data if isinstance(data, list) else []
    except FileNotFoundError:
        return []
    except json.JSONDecodeError:
        # If file is corrupted, return empty list
        return []


def save_clients(clients):
    os.makedirs(os.path.dirname(CLIENTS_FILE), exist_ok=True)
    with open(CLIENTS_FILE, "w") as f:
        json.dump(clients, f, default=str)


def load_conversation_states():
    try:
        with open(CONVERSATION_STATES_FILE, "r") as f:
            return json.load(f)
    except FileNotFoundError:
        return {}


def save_conversation_states(conversation_states):
    os.makedirs(os.path.dirname(CONVERSATION_STATES_FILE), exist_ok=True)
    with open(CONVERSATION_STATES_FILE, "w") as f:
        json.dump(conversation_states, f, default=str)
