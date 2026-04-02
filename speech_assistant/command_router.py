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
    }
}

def route_intent(intent, command):
    command = command.strip().lower()

    # 🔹 NAVIGATION (Web Core)
    if intent == "navigation" or "go back" in command or "return to main" in command:
        if "rag" in command:
            return "NAV:RAG"
        if "media" in command or "entertainment" in command:
            return "NAV:MEDIA"
        if "image" in command or "visual" in command:
            return "NAV:IMAGE_GEN"
        if "setting" in command or "profile" in command or "password" in command or "face" in command:
            return "NAV:SETTINGS"
        if "logout" in command or "sign out" in command:
            return "NAV:LOGOUT"
        if "dashboard" in command or "main" in command or "go back" in command:
            return "NAV:DASHBOARD"
    
    if "upload" in command or "pick files" in command:
        return "CMD:UPLOAD"

    # 🔹 OPEN / START APPLICATIONS
    for trigger in ["open ", "start "]:
        if command.startswith(trigger):
            app_name = command.replace(trigger, "").strip()
            if app_name in APPS:
                os.system(APPS[app_name]["open"])
                return f"Opening {app_name}."
            
            # Special case for web modules via "open"
            if "rag" in app_name: return "NAV:RAG"
            if "media" in app_name: return "NAV:MEDIA"
            if "code" in app_name: return "NAV:CODE"
            if "image" in app_name or "visual" in app_name: return "NAV:IMAGE_GEN"
            if "setting" in app_name or "profile" in app_name or "password" in app_name: return "NAV:SETTINGS"
            if "logout" in app_name or "sign out" in app_name: return "NAV:LOGOUT"

    # 🔹 CLOSE APPLICATIONS
    if command.startswith("close "):
        app_name = command.replace("close ", "").strip()
        if app_name in APPS:
            process_name = APPS[app_name]["process"]
            os.system(f"taskkill /IM {process_name} /F")
            return f"Closing {app_name}."

    # 🔹 TIME
    if intent == "ask_time":
        return f"The current time is {datetime.now().strftime('%H:%M')}"

    # 🔹 DATE
    if intent == "ask_date":
        return f"Today's date is {datetime.now().strftime('%Y-%m-%d')}"

    return None