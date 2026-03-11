import os
from datetime import datetime

# 🔹 Application Configuration
APPS = {
    "chrome": {
        "open": "start chrome",
        "process": "chrome.exe"
    },
    "edge": {
        "open": "start msedge",
        "process": "msedge.exe"
    },
    "notepad": {
        "open": "start notepad",
        "process": "notepad.exe"
    },
    "calculator": {
        "open": "start calc",
        "process": "CalculatorApp.exe"
    },
    "youtube": {
        "open": "start msedge https://www.youtube.com",
        "process": "msedge.exe"
    },
    "whatsapp": {
        "open": "start msedge https://web.whatsapp.com",
        "process": "msedge.exe"
    },
    "antigravity": {
        "open": "start antigravity",
        "process": "antigravity.exe"
    },
    "chat gpt": {
        "open": "start msedge https://chat.openai.com",
        "process": "msedge.exe"
    },
    "gemini": {
        "open": "start msedge https://gemini.google.com",
        "process": "msedge.exe"
    },
    "claude": {
        "open": "start msedge https://claude.ai",
        "process": "msedge.exe"
    }
}


def route_intent(intent, command):

    command = command.strip().lower()

    # 🔹 OPEN / START APPLICATIONS
    for trigger in ["open ", "start "]:
        if command.startswith(trigger):
            app_name = command.replace(trigger, "").strip()

            if app_name in APPS:
                os.system(APPS[app_name]["open"])
                return f"Opening {app_name}."

            return "Application not recognized."

    # 🔹 CLOSE APPLICATIONS
    if command.startswith("close "):
        app_name = command.replace("close ", "").strip()

        if app_name in APPS:
            process_name = APPS[app_name]["process"]
            os.system(f"taskkill /IM {process_name} /F")
            return f"Closing {app_name}."

        return "Application not recognized."

    # 🔹 TIME
    if intent == "ask_time":
        return f"The current time is {datetime.now().strftime('%H:%M')}"

    # 🔹 DATE
    if intent == "ask_date":
        return f"Today's date is {datetime.now().strftime('%Y-%m-%d')}"

    return None