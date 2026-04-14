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

    # 🔹 HIGH-PRIORITY MODULE NAVIGATION (Check Keywords with Navigation Verbs)
    nav_verbs = ["go to", "open", "access", "start", "switch to", "launch", "initiate"]
    
    def is_nav(cmd, keywords):
        cmd_low = cmd.lower()
        # Direct match
        if cmd_low in keywords: return True
        # Verb + keyword match
        for verb in nav_verbs:
            for kw in keywords:
                if f"{verb} {kw}" in cmd_low: return True
        return False

    if is_nav(command, ["rag", "intel", "rag intel"]):
        return "NAV:RAG"
    if is_nav(command, ["media", "entertainment", "movie", "video", "media box"]):
        return "NAV:MEDIA"
    if is_nav(command, ["image", "visual", "manifest", "image gen", "visualizer"]):
        return "NAV:IMAGE_GEN"
    if is_nav(command, ["code", "omni", "coder", "omni coder", "code assistant"]):
        return "NAV:CODE"
    if is_nav(command, ["setting", "profile", "password", "face"]):
        return "NAV:SETTINGS"
    if is_nav(command, ["logout", "sign out"]):
        return "NAV:LOGOUT"
    if is_nav(command, ["dashboard", "main", "go back"]):
        return "NAV:DASHBOARD"

    # 🔹 NAVIGATION INTENT (LLM Detected)
    if intent == "navigation" or "go back" in command or "return to main" in command:
        # Fallback if keywords missed
        if "rag" in command: return "NAV:RAG"
        if "media" in command: return "NAV:MEDIA"
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
    
    if intent == "image_gen":
        prompt = command.replace("generate", "").replace("create", "").replace("make", "").replace("image", "").replace("picture", "").replace("of ", "").replace("a ", "").replace("an ", "").strip()
        return f"GEN_IMAGE:{prompt}"

    # 🔹 TIME
    if intent == "ask_time":
        return f"The current time is {datetime.now().strftime('%H:%M')}"

    # 🔹 DATE
    if intent == "ask_date":
        return f"Today's date is {datetime.now().strftime('%Y-%m-%d')}"

    return None