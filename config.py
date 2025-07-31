# config.py - Complete configuration

# System commands
import os


SYSTEM_COMMANDS = {
    "shutdown": ["shutdown", "/s", "/t", "10"],
    "restart": ["shutdown", "/r", "/t", "10"],
    "sleep": ["rundll32.exe", "powrprof.dll,SetSuspendState", "0,1,0"],
    "lock": ["rundll32.exe", "user32.dll,LockWorkStation"],
    "logout": ["shutdown", "/l"],
    "hibernate": ["shutdown", "/h"]
}

# Application paths (Windows)
APP_PATHS = {
    "calculator": "calc.exe",
    "notepad": "notepad.exe",
    "command prompt": "cmd.exe",
    "task manager": "taskmgr.exe",
    "paint": "mspaint.exe",
    "word": "winword.exe",
    "excel": "excel.exe",
    "powerpoint": "powerpnt.exe",
    "outlook": "outlook.exe",
    "control panel": "control.exe",
    "file explorer": "explorer.exe",
    "photos": "ms-photos:",
    "camera": "microsoft.windows.camera:",
    "calendar": "outlookcal:"
}

# Special folders
SPECIAL_FOLDERS = {
    "documents": os.path.join(os.environ['USERPROFILE'], 'Documents'),
    "downloads": os.path.join(os.environ['USERPROFILE'], 'Downloads'),
    "pictures": os.path.join(os.environ['USERPROFILE'], 'Pictures'),
    "music": os.path.join(os.environ['USERPROFILE'], 'Music'),
    "videos": os.path.join(os.environ['USERPROFILE'], 'Videos'),
    "desktop": os.path.join(os.environ['USERPROFILE'], 'Desktop')
}

# Website URLs
WEB_URLS = {
    "youtube": "https://www.youtube.com",
    "google": "https://www.google.com",
    "gmail": "https://mail.google.com",
    "facebook": "https://www.facebook.com",
    "twitter": "https://twitter.com",
    "instagram": "https://www.instagram.com",
    "whatsapp": "https://web.whatsapp.com",
    "linkedin": "https://www.linkedin.com",
    "wikipedia": "https://www.wikipedia.org",
    "amazon": "https://www.amazon.com",
    "netflix": "https://www.netflix.com",
    "spotify": "https://www.spotify.com",
    "github": "https://www.github.com",
    "stackoverflow": "https://stackoverflow.com"
}

# All supported commands
CANDIDATE_INTENTS = [
    # System Controls
    "shutdown", "restart", "sleep", "lock", "logout", "hibernate",
    "system info", "battery status", "disk usage", "system diagnostics",
    
    # Application Controls
    "open calculator", "open notepad", "open command prompt",
    "open task manager", "open paint", "open word", "open excel",
    "open powerpoint", "open outlook", "open settings", "open control panel",
    "open file explorer", "open photos", "open camera", "open calendar", "open mail",
    
    # Folder Operations
    "open documents", "open downloads", "open pictures", "open music",
    "open videos", "open desktop",
    
    # Web Controls
    "open youtube", "open google", "open gmail", "open facebook",
    "open twitter", "open instagram", "open whatsapp", "open linkedin",
    "open wikipedia", "open amazon", "open netflix", "open spotify",
    "open github", "open stackoverflow", "search web", "search youtube",
    
    # Media Controls
    "play music", "pause music", "next track", "previous track",
    "increase volume", "decrease volume", "mute volume", "unmute volume",
    "set volume to", "take screenshot", "record screen", "start recording",
    "stop recording",
    
    # File Operations
    "list files", "create folder", "delete file", "copy file", "move file",
    "rename file", "open file", "show file info",
    
    # Productivity
    "current time", "current date", "set alarm", "set timer", "check calendar",
    "create reminder", "check weather", "check news", "create note",
    
    # Utilities
    "tell joke", "ip address", "what can you do", "help",
    "thank you", "who are you", "who made you", "how are you",
    
    # Gesture Controls
    "enable gestures", "disable gestures", "gesture help"
]

# Default gesture state
DEFAULT_GESTURE_STATE = {
    "active": False,
    "detected": None,
    "volume_level": 0.5,
    "brightness_level": 50,
    "mouse_control": False,
    "recording": False
}