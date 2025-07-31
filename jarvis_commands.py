import os
import time
import cv2
import pyautogui
import psutil
import webbrowser
import shutil
import pyjokes
import requests
import json
import screen_brightness_control as sbc
import win32gui
import win32con
import subprocess
import datetime
import platform
import socket
from pycaw.pycaw import AudioUtilities, ISimpleAudioVolume
from comtypes import CLSCTX_ALL
import wmi
from config import (CANDIDATE_INTENTS, SYSTEM_COMMANDS, APP_PATHS, 
                   WEB_URLS, SPECIAL_FOLDERS, DEFAULT_GESTURE_STATE)


def execute_specific_command(assistant, intent, command=None):
    """Execute specific commands based on intent"""
    # System Commands
    if intent in SYSTEM_COMMANDS:
        assistant.control_system(intent)
    elif intent == "system info":
        get_system_info(assistant)
    elif intent == "battery status":
        get_battery_status(assistant)
    
    # Application Commands
    elif intent.startswith("open ") and intent[5:] in APP_PATHS:
        open_application(assistant, intent[5:])
    elif intent.startswith("open ") and intent[5:] in SPECIAL_FOLDERS:
        open_special_folder(assistant, intent[5:])
    elif intent.startswith("open ") and intent[5:] in WEB_URLS:
        open_website(assistant, intent[5:])
    
    # Media Commands
    elif intent in ["play music", "pause music", "next track", "previous track"]:
        action = intent.split()[0]
        media_control(assistant, action)
    elif intent in ["increase volume", "decrease volume", "mute volume", "unmute volume"]:
        action = intent.split()[0]
        adjust_volume(assistant, action)
    elif intent == "take screenshot":
        take_screenshot(assistant)
    elif intent in ["start recording", "record screen"]:
        start_recording(assistant)
    elif intent in ["stop recording"]:
        stop_recording(assistant)
    
    # File Operations
    elif intent == "list files":
        list_files(assistant)
    elif intent == "create folder":
        create_folder(assistant)
    elif intent == "delete file":
        delete_file(assistant)
    
    # Productivity
    elif intent == "current time":
        get_current_time(assistant)
    elif intent == "current date":
        get_current_date(assistant)
    elif intent == "set timer":
        set_timer(assistant)
    elif intent == "tell joke":
        tell_joke(assistant)
    elif intent == "ip address":
        get_ip_address(assistant)
    
    # Utilities
    elif intent == "what can you do":
        show_capabilities(assistant)
    elif intent == "help":
        show_help(assistant)
    
    # Gesture Controls
    elif intent == "enable gestures":
        assistant.toggle_gestures(True)
    elif intent == "disable gestures":
        assistant.toggle_gestures(False)
    elif intent == "gesture help":
        assistant.speak("Supported gestures: thumbs up/down, volume up/down, brightness up/down")
    
    else:
        assistant.speak("I understood the command but haven't implemented that yet")

# =============== SYSTEM COMMANDS ===============
def control_system(assistant, action):
    if action not in SYSTEM_COMMANDS:
        return
        
    try:
        assistant.speak(f"Please confirm {action} with voice or thumbs up gesture")
        start_time = time.time()
        
        while time.time() - start_time < 3 and assistant.running:
            confirmation = assistant.listen(timeout=1)
            if confirmation and "confirm" in confirmation:
                subprocess.run(SYSTEM_COMMANDS[action])
                return
            
            if assistant.gesture_state.get("detected") == "thumbs_up":
                subprocess.run(SYSTEM_COMMANDS[action])
                return
            
            time.sleep(0.1)
        
        assistant.speak(f"{action} cancelled")
    except Exception as e:
        print(f"System control error: {e}")
        assistant.speak(f"Sorry, I couldn't {action} the system")

def get_system_info(assistant):
    """Enhanced system information with more details"""
    try:
        system = platform.uname()
        cpu = psutil.cpu_percent()
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('C:')
        battery = psutil.sensors_battery()
        boot_time = datetime.datetime.fromtimestamp(psutil.boot_time())
        
        info = f"""
        System: {system.system} {system.release}
        Machine: {system.machine}
        Processor: {system.processor}
        CPU Usage: {cpu}%
        Memory: {memory.percent}% used ({memory.used//(1024**2)}MB of {memory.total//(1024**2)}MB)
        Disk: {disk.percent}% used on C: drive
        Boot Time: {boot_time.strftime("%Y-%m-%d %H:%M:%S")}
        """
        
        if battery:
            info += f"Battery: {battery.percent}%"
            if battery.power_plugged:
                info += " (plugged in)"
            else:
                info += f" ({battery.secsleft//60} minutes remaining)"
        
        assistant.speak(info)
    except Exception as e:
        print(f"System info error: {e}")
        assistant.speak("Sorry, I couldn't get system information")

def get_battery_status(assistant):
    """Detailed battery information"""
    try:
        battery = psutil.sensors_battery()
        if battery:
            status = "plugged in" if battery.power_plugged else "on battery"
            assistant.speak(f"Battery is at {battery.percent}% and {status}")
            if not battery.power_plugged:
                assistant.speak(f"Estimated remaining time: {battery.secsleft//60} minutes")
        else:
            assistant.speak("No battery information available")
    except Exception as e:
        print(f"Battery error: {e}")
        assistant.speak("Sorry, I couldn't check battery status")

# =============== APPLICATION CONTROLS ===============
def open_application(assistant, app_name):
    """Open applications with error handling"""
    try:
        if app_name in APP_PATHS:
            subprocess.Popen(APP_PATHS[app_name])
            assistant.speak(f"Opening {app_name}")
        else:
            assistant.speak(f"I don't know how to open {app_name}")
    except Exception as e:
        print(f"Error opening {app_name}: {e}")
        assistant.speak(f"Sorry, I couldn't open {app_name}")

def open_special_folder(assistant, folder_name):
    """Open special system folders"""
    try:
        if folder_name in SPECIAL_FOLDERS:
            os.startfile(SPECIAL_FOLDERS[folder_name])
            assistant.speak(f"Opening {folder_name} folder")
        else:
            assistant.speak(f"I don't know how to open {folder_name} folder")
    except Exception as e:
        print(f"Folder error: {e}")
        assistant.speak(f"Sorry, I couldn't open {folder_name} folder")

# =============== WEB CONTROLS ===============
def open_website(assistant, site_name):
    """Open websites with error handling"""
    try:
        if site_name in WEB_URLS:
            webbrowser.open(WEB_URLS[site_name])
            assistant.speak(f"Opening {site_name}")
        else:
            assistant.speak(f"I don't know how to open {site_name}")
    except Exception as e:
        print(f"Error opening {site_name}: {e}")
        assistant.speak(f"Sorry, I couldn't open {site_name}")

def search_web(assistant, query=None):
    """Search the web with Google"""
    try:
        if not query:
            assistant.speak("What would you like to search for?")
            query = assistant.listen()
            if not query:
                return
        
        search_url = f"https://www.google.com/search?q={query}"
        webbrowser.open(search_url)
        assistant.speak(f"Searching the web for {query}")
    except Exception as e:
        print(f"Search error: {e}")
        assistant.speak("Sorry, I couldn't perform the search")

# =============== MEDIA CONTROLS ===============
def media_control(assistant, action):
    """Control media playback"""
    try:
        if action == "play":
            pyautogui.press('playpause')
            assistant.speak("Playing media")
        elif action == "pause":
            pyautogui.press('playpause')
            assistant.speak("Media paused")
        elif action == "next":
            pyautogui.press('nexttrack')
            assistant.speak("Next track")
        elif action == "previous":
            pyautogui.press('prevtrack')
            assistant.speak("Previous track")
    except Exception as e:
        print(f"Media control error: {e}")
        assistant.speak("Sorry, I couldn't control the media")

def adjust_volume(assistant, action=None, level=None):
    """Enhanced volume control with gesture support"""
    try:
        sessions = AudioUtilities.GetAllSessions()
        for session in sessions:
            volume = session._ctl.QueryInterface(ISimpleAudioVolume)
            if level is not None:
                volume.SetMasterVolume(level, None)
            elif action == "increase":
                current = volume.GetMasterVolume()
                volume.SetMasterVolume(min(current + 0.1, 1.0), None)
            elif action == "decrease":
                current = volume.GetMasterVolume()
                volume.SetMasterVolume(max(current - 0.1, 0.0), None)
            elif action == "mute":
                volume.SetMute(1, None)
            elif action == "unmute":
                volume.SetMute(0, None)
        
        if level is not None:
            assistant.speak(f"Volume set to {int(level*100)}%")
        elif action in ["increase", "decrease"]:
            assistant.speak(f"Volume {action}d")
        elif action in ["mute", "unmute"]:
            assistant.speak(f"Volume {action}d")
    except Exception as e:
        print(f"Volume adjustment error: {e}")
        assistant.speak("Sorry, I couldn't adjust the volume")

def take_screenshot(assistant):
    """Take and save screenshot"""
    try:
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"screenshot_{timestamp}.png"
        pyautogui.screenshot().save(filename)
        assistant.speak(f"Screenshot saved as {filename}")
    except Exception as e:
        print(f"Screenshot error: {e}")
        assistant.speak("Sorry, I couldn't take a screenshot")

def start_recording(assistant):
    """Start screen recording"""
    try:
        if assistant.recording:
            assistant.speak("Recording is already in progress")
            return
        
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        assistant.recording_filename = f"recording_{timestamp}.avi"
        screen_size = pyautogui.size()
        assistant.out = cv2.VideoWriter(assistant.recording_filename, assistant.fourcc, 20.0, screen_size)
        assistant.recording = True
        assistant.speak("Screen recording started")
    except Exception as e:
        print(f"Recording error: {e}")
        assistant.speak("Sorry, I couldn't start recording")

def stop_recording(assistant):
    """Stop screen recording"""
    try:
        if not assistant.recording:
            assistant.speak("No recording in progress")
            return
        
        assistant.recording = False
        assistant.out.release()
        assistant.speak(f"Screen recording saved as {assistant.recording_filename}")
    except Exception as e:
        print(f"Recording error: {e}")
        assistant.speak("Sorry, I couldn't stop recording")

# =============== FILE OPERATIONS ===============
def list_files(assistant, directory="."):
    """List files in a directory"""
    try:
        files = os.listdir(directory)
        if not files:
            assistant.speak("The directory is empty")
            return
        
        file_list = ", ".join(files[:5])  # Limit to first 5 files
        assistant.speak(f"Files in {directory}: {file_list}")
        if len(files) > 5:
            assistant.speak(f"There are {len(files)} total files")
    except Exception as e:
        print(f"Error listing files: {e}")
        assistant.speak("Sorry, I couldn't list the files")

def create_folder(assistant, folder_name=None):
    """Create a new folder"""
    try:
        if not folder_name:
            assistant.speak("What should I name the folder?")
            folder_name = assistant.listen()
            if not folder_name:
                return
        
        os.makedirs(folder_name, exist_ok=True)
        assistant.speak(f"Created folder: {folder_name}")
    except Exception as e:
        print(f"Error creating folder: {e}")
        assistant.speak(f"Sorry, I couldn't create the folder {folder_name}")

def delete_file(assistant, filename=None):
    """Delete a file"""
    try:
        if not filename:
            assistant.speak("Which file should I delete?")
            filename = assistant.listen()
            if not filename:
                return
        
        if os.path.exists(filename):
            os.remove(filename)
            assistant.speak(f"Deleted file: {filename}")
        else:
            assistant.speak(f"File {filename} not found")
    except Exception as e:
        print(f"Error deleting file: {e}")
        assistant.speak(f"Sorry, I couldn't delete {filename}")

# =============== PRODUCTIVITY ===============
def get_current_time(assistant):
    """Get current time with timezone"""
    now = datetime.datetime.now()
    assistant.speak(f"The current time is {now.strftime('%I:%M %p')}")

def get_current_date(assistant):
    """Get current date with day"""
    now = datetime.datetime.now()
    assistant.speak(f"Today is {now.strftime('%A, %B %d, %Y')}")

def set_timer(assistant, duration=None):
    """Set a timer"""
    try:
        if not duration:
            assistant.speak("For how many minutes?")
            duration = assistant.listen()
            if not duration:
                return
            
            # Extract numbers from spoken duration
            try:
                minutes = int(''.join(filter(str.isdigit, duration)))
            except:
                minutes = 1
        else:
            minutes = int(duration)
        
        assistant.speak(f"Timer set for {minutes} minutes")
        time.sleep(minutes * 60)
        assistant.speak("Time's up! Your timer has finished")
    except Exception as e:
        print(f"Timer error: {e}")
        assistant.speak("Sorry, I couldn't set the timer")

def tell_joke(assistant):
    """Tell a random joke"""
    joke = pyjokes.get_joke()
    assistant.speak(joke)

# =============== UTILITIES ===============
def get_ip_address(assistant):
    """Get public IP address"""
    try:
        response = requests.get('https://api.ipify.org?format=json')
        ip = response.json()['ip']
        assistant.speak(f"Your public IP address is {ip}")
    except Exception as e:
        print(f"IP address error: {e}")
        assistant.speak("Sorry, I couldn't retrieve your IP address")

def show_help(assistant):
    """Show help information"""
    categories = {
        "System": ["shutdown", "restart", "lock", "system info"],
        "Apps": ["open calculator", "open notepad", "open command prompt"],
        "Web": ["open youtube", "open google", "search web"],
        "Media": ["play music", "increase volume", "take screenshot"],
        "Productivity": ["current time", "current date", "set timer"],
        "Utilities": ["tell joke", "ip address", "what can you do"]
    }
    
    assistant.speak("Here are the main command categories:")
    for category, commands in categories.items():
        assistant.speak(f"{category}: {', '.join(commands[:3])}...")
    assistant.speak("Say 'what can you do' for full command list")

def show_capabilities(assistant):
    """Show all capabilities"""
    assistant.speak("I can perform these actions:")
    for i, intent in enumerate(sorted(CANDIDATE_INTENTS), 1):
        if i % 5 == 0:  # Pause every 5 commands
            time.sleep(1)
        print(f"- {intent}")
    assistant.speak("That's all I can do for now!")