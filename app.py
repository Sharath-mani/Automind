import threading
import time
import os
import pyttsx3
import speech_recognition as sr
from transformers import pipeline, logging
from gesture import gesture_recognition
from config import (CANDIDATE_INTENTS, SYSTEM_COMMANDS, APP_PATHS, 
                   WEB_URLS, SPECIAL_FOLDERS, DEFAULT_GESTURE_STATE)

# Suppress transformer warnings
logging.set_verbosity_error()

class JarvisAssistant:
    def __init__(self):
        self.classifier = self._initialize_classifier()
        self.engine = self._initialize_speech_engine()
        self.recognizer = sr.Recognizer()
        self.gesture_state = DEFAULT_GESTURE_STATE.copy()
        self.running = True
        self.setup_gesture_control()
        
    def _initialize_classifier(self):
        try:
            return pipeline("zero-shot-classification", model="facebook/bart-large-mnli")
        except Exception as e:
            print(f"Model loading error: {e}")
            return None
            
    def _initialize_speech_engine(self):
        engine = pyttsx3.init()
        voices = engine.getProperty('voices')
        engine.setProperty('voice', voices[1].id)  # Change index for different voices
        engine.setProperty('rate', 160)
        engine.setProperty('volume', 1.0)
        return engine
        
    def setup_gesture_control(self):
        """Initialize gesture control in a separate thread"""
        self.gesture_thread = threading.Thread(
            target=gesture_recognition,
            args=(self.gesture_state,),
            daemon=True
        )
        self.gesture_thread.start()
        
    def speak(self, text):
        """Convert text to speech with error handling"""
        print(f"Jarvis: {text}")
        try:
            self.engine.say(text)
            self.engine.runAndWait()
        except Exception as e:
            print(f"Speech error: {e}")
    
    def listen(self, timeout=5):
        """Improved listening with continuous monitoring"""
        with sr.Microphone() as source:
            self.recognizer.adjust_for_ambient_noise(source, duration=1)
            print("Listening...")
            try:
                audio = self.recognizer.listen(source, timeout=timeout)
                text = self.recognizer.recognize_google(audio).lower()
                print(f"You said: {text}")
                return text
            except sr.WaitTimeoutError:
                return None
            except sr.UnknownValueError:
                self.speak("I didn't catch that. Could you repeat?")
                return None
            except sr.RequestError:
                self.speak("Speech service unavailable. Please check your internet connection.")
                return None
            except Exception as e:
                print(f"Listening error: {e}")
                return None
    
    def handle_gestures(self):
        """Process detected gestures"""
        if not self.gesture_state['active']:
            return
        
        gesture = self.gesture_state.get('detected')
        if not gesture:
            return
        
        try:
            if gesture == "volume_up":
                self.adjust_volume("increase")
            elif gesture == "volume_down":
                self.adjust_volume("decrease")
            elif gesture == "thumbs_up":
                self.speak("Gesture confirmed!")
            elif gesture == "thumbs_down":
                self.speak("Gesture rejected!")
            elif gesture == "brightness_up":
                self.adjust_brightness(delta=25)
            elif gesture == "brightness_down":
                self.adjust_brightness(delta=25)
            
            # Reset gesture after handling
            self.gesture_state['detected'] = None
        except Exception as e:
            print(f"Gesture handling error: {e}")
    
    def toggle_gestures(self, enable=True):
        """Enable or disable gesture control"""
        self.gesture_state['active'] = enable
        status = "enabled" if enable else "disabled"
        self.speak(f"Gesture control {status}")
    
    def execute_command(self, command):
        """Execute commands with improved handling"""
        if not command:
            return
        
        # Handle gesture commands first
        self.handle_gestures()
        
        # Special case for volume set commands
        if "set volume to" in command:
            try:
                level = int(''.join(filter(str.isdigit, command))) / 100
                self.adjust_volume(level=level)
                return
            except:
                self.speak("Please specify a volume level between 0 and 100")
                return
        
        # Classify the intent
        intent, confidence = None, 0
        for possible_intent in CANDIDATE_INTENTS:
            if possible_intent in command:
                intent = possible_intent
                confidence = 1.0
                break
        
        if not intent and self.classifier:
            try:
                result = self.classifier(command, CANDIDATE_INTENTS)
                intent, confidence = result['labels'][0], result['scores'][0]
            except Exception as e:
                print(f"Classification error: {e}")
        
        print(f"Detected intent: {intent} (confidence: {confidence:.2f})")
        
        if confidence > 0.5:
            from jarvis_commands import execute_specific_command
            execute_specific_command(self, intent, command)
        else:
            self.speak("I didn't understand.")
    
    def run(self):
        """Main execution loop"""
        self.speak("Jarvis assistant activated. How can I help you today?")
        print("Say 'exit' to quit or 'help' for commands list")
        
        try:
            while self.running:
                command = self.listen()
                
                if command:
                    if "exit" in command or "quit" in command:
                        self.running = False
                        break
                    
                    self.execute_command(command)
                
                # Small delay to prevent CPU overuse
                time.sleep(0.1)
                
        except KeyboardInterrupt:
            self.running = False
        finally:
            self.gesture_state['active'] = False
            self.speak("Goodbye!")
            if self.gesture_thread.is_alive():
                self.gesture_thread.join(timeout=1)

if __name__ == "__main__":
    assistant = JarvisAssistant()
    assistant.run()