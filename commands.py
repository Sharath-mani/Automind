import os
import shutil
import pyttsx3
import webbrowser
import psutil
import pyautogui
from transformers import pipeline
import spacy
import speech_recognition as sr
import win32com.client
import pygetwindow as gw
from pycaw.pycaw import AudioUtilities, ISimpleAudioVolume
from comtypes import CLSCTX_ALL


# Initialize voice engine
engine = pyttsx3.init()
engine.setProperty('rate', 160)
nlp = spacy.load("en_core_web_sm")
classifier = pipeline("zero-shot-classification", model="roberta-large-mnli")

# Candidate intents
CANDIDATE_INTENTS = [
    "open browser", "search web", "play music", "monitor system",
    "control brightness", "restart wifi", "shutdown", "open file",
    "copy file", "move file", "extract text", "write in word", "exit",
    "maximize window", "minimize window", "open calculator", "open settings", "take screenshot"
    "increase volume", "decrease volume", "mute volume", "unmute volume"

]

def speak(text):
    """Speak out the provided text."""
    engine.say(text)
    engine.runAndWait()

def listen():
    """Listen for audio input using the microphone and return recognized text."""
    recognizer = sr.Recognizer()
    with sr.Microphone() as source:
        recognizer.adjust_for_ambient_noise(source)
        speak("Listening...")
        try:
            audio = recognizer.listen(source, timeout=10)
            return recognizer.recognize_google(audio).lower()
        except:
            return ""

def dependency_parse(command):
    """Use spaCy to extract numerical parameters from the command."""
    doc = nlp(command)
    numbers = [int(token.text) for token in doc if token.like_num]
    return {"numbers": numbers, "doc": doc}

def classify_intent(command):
    """Use RoBERTa zero-shot classification to determine intent."""
    result = classifier(command, CANDIDATE_INTENTS)
    return result['labels'][0], result['scores'][0]

def execute_command(command):
    """Execute the command based on the user's intent."""
    dep_info = dependency_parse(command)
    intent, score = classify_intent(command)

    if score < 0.3:
        speak("I'm not sure what you mean.")
        return

    INTENT_FUNCTIONS = {
        "open browser": open_browser,
        "search web": lambda: search_web(command.replace("search", "").strip()),
        "play music": lambda: play_music(command.replace("play", "").strip()),
        "monitor system": monitor_system,
        "control brightness": lambda: control_brightness(dep_info["numbers"][0] if dep_info["numbers"] else 50),
        "restart wifi": restart_wifi,
        "shutdown": lambda: control_system("shutdown"),
        "maximize window": maximize_window,
        "minimize window": minimize_window,
        "open calculator": open_calculator,
        "open settings": open_settings,
        "take screenshot": take_screenshot,
        "increase volume": increase_volume,
        "decrease volume": decrease_volume,
        "mute volume": mute_volume,
        "unmute volume": unmute_volume
    }

    if intent in INTENT_FUNCTIONS:
        INTENT_FUNCTIONS[intent]()
    else:
        speak("Command not supported.")

def command_listener():
    """Listen and process commands."""
    speak("Hello! How can I assist you?")
    while True:
        command = listen()
        if command:
            execute_command(command)

# Individual Command Functions
def open_browser():
    """Open a browser."""
    webbrowser.open("https://www.google.com")
    speak("Opening the browser.")

def search_web(query):
    """Search the web with a query."""
    webbrowser.open(f"https://www.google.com/search?q={query}")
    speak(f"Searching for {query}.")

def play_music(song):
    """Play music on YouTube."""
    try:
        import pywhatkit
        pywhatkit.playonyt(song)
        speak(f"Playing {song} on YouTube.")
    except ImportError:
        speak("Sorry, the required module to play music is not installed.")

def monitor_system():
    """Monitor the system's health."""
    cpu = psutil.cpu_percent(interval=1)
    ram = psutil.virtual_memory().percent
    speak(f"System health: CPU usage is at {cpu}% and RAM usage is at {ram}%.")

def control_brightness(level):
    """Control screen brightness."""
    speak(f"Setting brightness to {level} percent.")
    # This requires specific OS-dependent implementations.

def restart_wifi():
    """Restart WiFi connection."""
    speak("Restarting WiFi.")
    os.system("netsh interface set interface name='Wi-Fi' admin=disable")
    os.system("netsh interface set interface name='Wi-Fi' admin=enable")
    speak("WiFi restarted.")

def control_system(action):
    """Control the system (shutdown, restart, etc.)."""
    if action == "shutdown":
        speak("Shutting down the system.")
        os.system("shutdown /s /t 1")
    elif action == "restart":
        speak("Restarting the system.")
        os.system("shutdown /r /t 1")

def maximize_window():
    """Maximize the active window."""
    try:
        window = gw.getActiveWindow()
        if window:
            window.maximize()
            speak("Window maximized.")
        else:
            speak("No active window found.")
    except Exception as e:
        print(e)
        speak("Unable to maximize the window.")

def minimize_window():
    """Minimize the active window."""
    try:
        window = gw.getActiveWindow()
        if window:
            window.minimize()
            speak("Window minimized.")
        else:
            speak("No active window found.")
    except Exception as e:
        print(e)
        speak("Unable to minimize the window.")

def open_calculator():
    """Open the calculator."""
    try:
        if os.name == "nt":
            os.system("start calc")
        elif os.name == "posix":
            os.system("gnome-calculator")
        speak("Opening calculator.")
    except Exception as e:
        print(e)
        speak("Failed to open calculator.")

def open_settings():
    """Open the system settings."""
    try:
        if os.name == "nt":
            os.system("start ms-settings:")
        elif os.name == "posix":
            os.system("gnome-control-center")
        speak("Opening settings.")
    except Exception as e:
        print(e)
        speak("Failed to open settings.")

def take_screenshot():
    """Take a screenshot."""
    try:
        screenshot = pyautogui.screenshot()
        filepath = os.path.join(os.getcwd(), "screenshot.png")
        screenshot.save(filepath)
        speak(f"Screenshot saved at {filepath}.")
    except Exception as e:
        print(e)
        speak("Failed to take screenshot.")

def set_volume(level):
    """Set volume to a specific level (0-100)."""
    sessions = AudioUtilities.GetAllSessions()
    for session in sessions:
        if session.Process and session.Process.name() == "System":
            volume = session._ctl.QueryInterface(ISimpleAudioVolume)
            volume.SetMasterVolume(level / 100.0, None)
    speak(f"Volume set to {level} percent.")

def increase_volume():
    """Increase system volume by 10%."""
    sessions = AudioUtilities.GetAllSessions()
    for session in sessions:
        if session.Process and session.Process.name() == "System":
            volume = session._ctl.QueryInterface(ISimpleAudioVolume)
            current_volume = volume.GetMasterVolume() * 100
            new_volume = min(100, current_volume + 10)
            volume.SetMasterVolume(new_volume / 100.0, None)
    speak("Volume increased.")

def decrease_volume():
    """Decrease system volume by 10%."""
    sessions = AudioUtilities.GetAllSessions()
    for session in sessions:
        if session.Process and session.Process.name() == "System":
            volume = session._ctl.QueryInterface(ISimpleAudioVolume)
            current_volume = volume.GetMasterVolume() * 100
            new_volume = max(0, current_volume - 10)
            volume.SetMasterVolume(new_volume / 100.0, None)
    speak("Volume decreased.")

def mute_volume():
    """Mute the system volume."""
    sessions = AudioUtilities.GetAllSessions()
    for session in sessions:
        if session.Process and session.Process.name() == "System":
            volume = session._ctl.QueryInterface(ISimpleAudioVolume)
            volume.SetMasterVolume(0, None)
    speak("System volume muted.")

def unmute_volume():
    """Unmute the system volume (set to 50%)."""
    sessions = AudioUtilities.GetAllSessions()
    for session in sessions:
        if session.Process and session.Process.name() == "System":
            volume = session._ctl.QueryInterface(ISimpleAudioVolume)
            volume.SetMasterVolume(0.5, None)
    speak("System volume unmuted.")