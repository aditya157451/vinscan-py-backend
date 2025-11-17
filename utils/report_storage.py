import json
import os
from typing import Optional, Dict, Any
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "../data")
REPORTS_FILE = os.path.join(DATA_DIR, "reports.json")

# Ensure data directory exists
os.makedirs(DATA_DIR, exist_ok=True)

# Recreate the reports file (fix corruption)
with open(REPORTS_FILE, "w") as f:
    json.dump({}, f, indent=2)


def datetime_serializer(obj):
    """JSON serializer for datetime objects not serializable by default json code"""
    if isinstance(obj, datetime):
        return obj.isoformat()
    raise TypeError("Type not serializable")


async def save_report_to_database(report: Dict[str, Any]) -> None:
    """
    Save or update a report by clientId in the JSON database.
    """
    try:
        # Load existing reports
        try:
            with open(REPORTS_FILE, "r", encoding="utf-8") as f:
                reports = json.load(f)
        except json.JSONDecodeError:
            # If file is corrupted, start with empty dict
            reports = {}

        # Update with new report
        reports[report["clientId"]] = report

        # Write back with custom serializer
        with open(REPORTS_FILE, "w", encoding="utf-8") as f:
            json.dump(reports, f, indent=2, default=datetime_serializer)
    except Exception as e:
        print("Error saving report:", e)
        raise


async def get_report_by_client_id(client_id: str) -> Optional[Dict[str, Any]]:
    """
    Retrieve a report by clientId from the JSON database.
    """
    try:
        with open(REPORTS_FILE, "r", encoding="utf-8") as f:
            reports = json.load(f)

        return reports.get(client_id)
    except Exception as e:
        print("Error getting report:", e)
        return None
