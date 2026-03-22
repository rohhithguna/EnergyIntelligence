import os

from data.loader import load_data


TIME_COLUMNS = ["time", "timestamp", "datetime", "event_time", "date"]
VALUE_COLUMNS = ["data_rate", "usage"]


def validate_file(file_path):
    if not os.path.exists(file_path):
        return {"valid": False, "reason": "File not found"}

    ext = os.path.splitext(file_path)[1].lower()
    if ext not in [".csv", ".xlsx", ".xls"]:
        return {"valid": False, "reason": "Unsupported file type"}

    try:
        df = load_data(file_path)
    except Exception as exc:
        return {"valid": False, "reason": f"File is not readable: {exc}"}

    cols = [str(c).strip().lower().replace(" ", "_") for c in df.columns]
    if not any(c in TIME_COLUMNS for c in cols):
        return {"valid": False, "reason": "Missing time column"}

    if not any(c in VALUE_COLUMNS for c in cols):
        return {"valid": False, "reason": "Missing numeric column: data_rate or usage"}

    return {"valid": True, "reason": ""}
