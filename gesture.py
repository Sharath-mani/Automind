import cv2
import mediapipe as mp
import pyautogui
import numpy as np
import time
import math

# Declare mouse tracking variables as global here (to avoid the nonlocal SyntaxError)
prev_mouse_x, prev_mouse_y = None, None
smooth_mouse_x, smooth_mouse_y = None, None
mouse_sensitivity = 2.0 # Can also be global if it's truly a constant

def gesture_recognition(gesture_state):
    """Enhanced gesture recognition with scrolling, thumbs up/down, swipe left/right, and volume control."""
    mp_hands = mp.solutions.hands
    mp_drawing = mp.solutions.drawing_utils

    # Configure camera
    cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
    cap.set(cv2.CAP_PROP_FPS, 30)   # Optimal balance between smoothness and performance

    # Initialize gesture state (already done in main, but ensures local state for the thread)
    gesture_state["active"] = True

    # Scroll control parameters
    scroll_active = False
    base_angle = None # Reference angle when scrolling starts
    angle_threshold = 5  # Degrees - Smaller to make it more sensitive
    scroll_sensitivity = 100 # Increased sensitivity for faster scrolling (adjust as needed, was 20)
    last_scroll_time = time.time()
    scroll_cooldown = 0.2 # Faster response, allows more frequent scrolls (was 0.03)
    last_valid_angle = None # To prevent errors from invalid angle calculations
    scroll_buffer = 0    # Accumulates small scroll amounts for smoother increments
    smoothing_factor = 0.2 # Reduced smoothing for slightly quicker reaction (was 0.3)

    # Swipe control parameters
    swipe_threshold = 0.015 # Normalized distance to trigger swipe (was 0.05). Adjust this based on screen width
    last_hand_x = None
    last_swipe_time = time.time()
    swipe_cooldown = 0.2  # Prevents duplicate swipes

    # Gesture detection parameters
    gesture_cooldown = 0.7 # Time between gesture detections (e.g., thumbs up) (was 1.0)
    last_gesture_time = time.time()

    def calculate_angle(vec1, vec2):
        """Optimized angle calculation with safety checks."""
        nonlocal last_valid_angle
        try:
            dot_product = np.dot(vec1, vec2)
            norm_product = np.linalg.norm(vec1) * np.linalg.norm(vec2)

            if norm_product < 0.001:  # Prevent division by near-zero
                return last_valid_angle or 0

            # Clamp cos_angle to ensure it's within valid range for acos
            cos_angle = max(-1.0, min(1.0, dot_product / norm_product))
            angle = math.degrees(math.acos(cos_angle))
            last_valid_angle = angle
            return angle
        except Exception: # Catch any other potential math errors
            return last_valid_angle or 0

    def detect_thumbs_gesture(hand_landmarks):
        """Detect thumbs up or thumbs down gesture."""
        thumb_tip = hand_landmarks.landmark[mp_hands.HandLandmark.THUMB_TIP]
        thumb_ip = hand_landmarks.landmark[mp_hands.HandLandmark.THUMB_IP] # Intermediate Phalange
        thumb_mcp = hand_landmarks.landmark[mp_hands.HandLandmark.THUMB_MCP] # Metacarpophalangeal

        # Check if thumb is significantly extended (tip further from base than IP)
        # and generally pointing upwards or downwards relative to the MCP
        thumb_extended_vertically = thumb_tip.y < thumb_ip.y and thumb_tip.y < thumb_mcp.y

        # Check if other fingers are curled (tips are below their PIPs/MCPs)
        fingers_curled = True
        finger_check_points = [
            (mp_hands.HandLandmark.INDEX_FINGER_TIP, mp_hands.HandLandmark.INDEX_FINGER_PIP),
            (mp_hands.HandLandmark.MIDDLE_FINGER_TIP, mp_hands.HandLandmark.MIDDLE_FINGER_PIP),
            (mp_hands.HandLandmark.RING_FINGER_TIP, mp_hands.HandLandmark.RING_FINGER_PIP),
            (mp_hands.HandLandmark.PINKY_TIP, mp_hands.HandLandmark.PINKY_PIP)
        ]
        for tip, pip in finger_check_points:
            # Check if tip is significantly below PIP (meaning curled)
            if hand_landmarks.landmark[tip].y < hand_landmarks.landmark[pip].y - 0.02: # Added small buffer
                fingers_curled = False
                break
        
        # Additional check: thumb tip x relative to thumb MCP x for horizontal extension (avoids false positives)
        thumb_extended_horizontally = abs(thumb_tip.x - thumb_mcp.x) > 0.05 # Adjust threshold as needed

        if thumb_extended_vertically and fingers_curled and thumb_extended_horizontally:
            wrist_y = hand_landmarks.landmark[mp_hands.HandLandmark.WRIST].y
            # Thumbs up: thumb tip significantly above wrist, and not too far left/right of palm
            if thumb_tip.y < wrist_y - 0.15: # More aggressive threshold
                return "thumbs_up"
            # Thumbs down: thumb tip significantly below wrist
            elif thumb_tip.y > wrist_y + 0.15: # More aggressive threshold
                return "thumbs_down"

        return None


    def detect_swipe(hand_landmarks, frame_width):
        """Detect horizontal swipes."""
        nonlocal last_hand_x, last_swipe_time
        current_time = time.time()

        # Get the hand center position (e.g., wrist x-coordinate)
        # Using normalized coordinates for current_x
        current_x = hand_landmarks.landmark[mp_hands.HandLandmark.WRIST].x # Normalized x-coord

        if last_hand_x is not None and current_time - last_swipe_time > swipe_cooldown:
            # Calculate delta_x in proportion to screen width for consistent sensitivity
            # MediaPipe coords are 0 to 1, so `delta_x` is already normalized
            delta_x = current_x - last_hand_x

            # Swipe threshold is now based on normalized coordinates (e.g., 7% of screen width)
            if delta_x > swipe_threshold: # Moved significantly right
                last_swipe_time = current_time
                return "swipe_right"
            elif delta_x < -swipe_threshold: # Moved significantly left
                last_swipe_time = current_time
                return "swipe_left"

        last_hand_x = current_x
        return None

    def detect_open_palm(hand_landmarks):
        """Detect open palm gesture for volume control and potentially mouse control."""
        fingers_open = 0
        finger_tips = [
            mp_hands.HandLandmark.THUMB_TIP,
            mp_hands.HandLandmark.INDEX_FINGER_TIP,
            mp_hands.HandLandmark.MIDDLE_FINGER_TIP,
            mp_hands.HandLandmark.RING_FINGER_TIP,
            mp_hands.HandLandmark.PINKY_TIP
        ]
        finger_pips = [
            mp_hands.HandLandmark.THUMB_IP, # For thumb, check IP
            mp_hands.HandLandmark.INDEX_FINGER_PIP,
            mp_hands.HandLandmark.MIDDLE_FINGER_PIP,
            mp_hands.HandLandmark.RING_FINGER_PIP,
            mp_hands.HandLandmark.PINKY_PIP
        ]
        finger_mcps = [
            mp_hands.HandLandmark.THUMB_MCP, # For thumb, check MCP
            mp_hands.HandLandmark.INDEX_FINGER_MCP,
            mp_hands.HandLandmark.MIDDLE_FINGER_MCP,
            mp_hands.HandLandmark.RING_FINGER_MCP,
            mp_hands.HandLandmark.PINKY_MCP
        ]

        # Check if fingers are generally straight and tips are above their PIPs/MCPs
        for i, (tip_idx, pip_idx, mcp_idx) in enumerate(zip(finger_tips, finger_pips, finger_mcps)):
            # For thumb, check tip relative to IP or MCP base (horizontal for extension)
            if i == 0: # Thumb
                # Check if thumb tip is sufficiently to the side of the MCP (extended outward)
                if abs(hand_landmarks.landmark[tip_idx].x - hand_landmarks.landmark[mcp_idx].x) > 0.05:
                    fingers_open += 1
            else: # Other fingers
                # Check if tip is significantly above PIP (meaning open/straight)
                if hand_landmarks.landmark[tip_idx].y < hand_landmarks.landmark[pip_idx].y - 0.01: # Small buffer
                    fingers_open += 1
        
        # Check distance between thumb tip and pinky tip to ensure palm is open and spread
        thumb_tip = hand_landmarks.landmark[mp_hands.HandLandmark.THUMB_TIP]
        pinky_tip = hand_landmarks.landmark[mp_hands.HandLandmark.PINKY_TIP]
        distance = math.sqrt((thumb_tip.x - pinky_tip.x)**2 + (thumb_tip.y - pinky_tip.y)**2)
        
        # A threshold for open palm distance (normalized coords)
        is_palm_spread = distance > 0.15 # Adjust if needed

        return fingers_open >= 4 and is_palm_spread

    with mp_hands.Hands(
        max_num_hands=1,
        min_detection_confidence=0.7,
        min_tracking_confidence=0.7,
        static_image_mode=False
    ) as hands:
        prev_time = time.time()
        results = None  # Initialize results here

        # --- GLOBAL DECLARATIONS FOR MOUSE TRACKING ---
        # These variables are now declared global at the module level.
        # We need to tell this function that it will be *modifying* the global versions.
        global prev_mouse_x, prev_mouse_y, smooth_mouse_x, smooth_mouse_y
        global mouse_sensitivity # If you want to modify this globally later

        while gesture_state["active"]:
            current_time = time.time()
            ret, frame = cap.read()
            if not ret:
                continue

            # Skip some processing if we're running behind
            if current_time - prev_time < 0.025:   # Aim for closer to 40fps (1/40 = 0.025)
                continue
            prev_time = current_time

            frame = cv2.flip(frame, 1)
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

            # Process only every other frame to reduce load (this is fine)
            if int(current_time * 10) % 2 == 0:
                results = hands.process(rgb_frame)
            # Else: keep using the previous results

            # Reset detected gesture for this frame, unless it's continuous like volume/mouse
            gesture_state["detected"] = None

            # Check if we have any results to process
            if results is not None and results.multi_hand_landmarks:
                for hand_landmarks in results.multi_hand_landmarks:
                    # Draw hand landmarks for visual feedback
                    mp_drawing.draw_landmarks(
                        frame,
                        hand_landmarks,
                        mp_hands.HAND_CONNECTIONS,
                        mp_drawing.DrawingSpec(color=(0, 255, 0), thickness=2, circle_radius=4),
                        mp_drawing.DrawingSpec(color=(0, 0, 255), thickness=2)
                    )

                    # Check for thumbs up/down gestures
                    if current_time - last_gesture_time > gesture_cooldown:
                        thumb_gesture = detect_thumbs_gesture(hand_landmarks)
                        if thumb_gesture:
                            gesture_state["detected"] = thumb_gesture
                            last_gesture_time = current_time
                            cv2.putText(frame, thumb_gesture.upper(), (10, 90),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 0, 0), 2)

                    # Check for swipe gestures
                    swipe_gesture = detect_swipe(hand_landmarks, frame.shape[1])
                    if swipe_gesture and current_time - last_gesture_time > swipe_cooldown:
                        gesture_state["detected"] = swipe_gesture
                        last_gesture_time = current_time
                        cv2.putText(frame, swipe_gesture.upper(), (10, 120),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)

                        # Simulate arrow key press for swipe gestures
                        if swipe_gesture == "swipe_left":
                            pyautogui.press('left')
                        elif swipe_gesture == "swipe_right":
                            pyautogui.press('right')

                    # Check for scroll gesture (index finger)
                    mcp = hand_landmarks.landmark[mp_hands.HandLandmark.INDEX_FINGER_MCP]
                    pip = hand_landmarks.landmark[mp_hands.HandLandmark.INDEX_FINGER_PIP]
                    tip = hand_landmarks.landmark[mp_hands.HandLandmark.INDEX_FINGER_TIP]

                    # Calculate vectors and angle
                    vec1 = np.array([pip.x - mcp.x, pip.y - mcp.y])
                    vec2 = np.array([tip.x - pip.x, tip.y - pip.y])
                    angle = calculate_angle(vec1, vec2)

                    # Scrolling logic: Only activate if the index finger is relatively straight (angle < 25 degrees)
                    # and the middle finger is curled (to distinguish from open palm for mouse control/volume)
                    middle_tip = hand_landmarks.landmark[mp_hands.HandLandmark.MIDDLE_FINGER_TIP]
                    middle_pip = hand_landmarks.landmark[mp_hands.HandLandmark.MIDDLE_FINGER_PIP]
                    is_middle_finger_curled = middle_tip.y > middle_pip.y + 0.03 # Tip below PIP

                    if angle is not None and angle < 25 and is_middle_finger_curled: # Reduced angle for more precise trigger
                        if base_angle is None:
                            base_angle = angle # Initialize base angle when gesture starts

                        angle_diff = angle - base_angle

                        # Adjust scroll_buffer more directly with sensitivity
                        scroll_buffer += angle_diff * scroll_sensitivity * smoothing_factor

                        current_time = time.time()
                        if current_time - last_scroll_time > scroll_cooldown:
                            if abs(scroll_buffer) >= 1: # Only scroll when buffer accumulates enough
                                scroll_amount = int(scroll_buffer)
                                # Positive angle_diff (finger bending more) means scroll DOWN.
                                # Negative angle_diff (finger straightening) means scroll UP.
                                pyautogui.scroll(scroll_amount) # Removed '-' to make bending scroll down
                                scroll_buffer -= scroll_amount # Deduct scrolled amount from buffer
                                last_scroll_time = current_time
                                scroll_active = True
                        
                        # Gradually adjust base_angle to prevent drift and make it relative to current position
                        base_angle = base_angle * (1 - smoothing_factor) + angle * smoothing_factor

                    else: # If index finger is not straight or middle finger not curled, reset scrolling
                        scroll_active = False
                        base_angle = None # Reset base angle for new gesture
                        scroll_buffer = 0   # Reset buffer when not scrolling

                    # Check for volume control/mouse control gesture (open palm)
                    if detect_open_palm(hand_landmarks):
                        # If mouse control is active, override volume control for this gesture
                        if gesture_state["mouse_control"]:
                            # These variables are now global, so just assign to them directly
                            # No 'nonlocal' needed within this block anymore for these variables
                            gesture_state["detected"] = "mouse_move"
                            index_finger_tip = hand_landmarks.landmark[mp_hands.HandLandmark.INDEX_FINGER_TIP]
                            # Convert normalized coordinates to screen coordinates
                            screen_x = int(index_finger_tip.x * pyautogui.size().width)
                            screen_y = int(index_finger_tip.y * pyautogui.size().height)

                            # Smooth mouse movement
                            if smooth_mouse_x is None: # Check for initial state with None
                                smooth_mouse_x, smooth_mouse_y = float(screen_x), float(screen_y) # Initialize as float
                            else:
                                smooth_mouse_x = smooth_mouse_x * (1 - smoothing_factor) + screen_x * smoothing_factor
                                smooth_mouse_y = smooth_mouse_y * (1 - smoothing_factor) + screen_y * smoothing_factor

                            pyautogui.moveTo(smooth_mouse_x, smooth_mouse_y)
                            cv2.putText(frame, "MOUSE CONTROL", (10, 150),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 0), 2)
                        else: # If mouse control is not active, use for volume
                            # Get the palm height (y-coordinate) for volume level
                            palm_y = hand_landmarks.landmark[mp_hands.HandLandmark.WRIST].y
                            # Value will be between 0-1 (inverted because y increases downward)
                            volume_level = 1 - (palm_y * 1.3)  # Scale for better range
                            volume_level = max(0, min(1, volume_level))  # Clamp between 0-1

                            # Store the detected volume level in the gesture state
                            gesture_state["volume_level"] = volume_level
                            gesture_state["detected"] = "volume_control" # Signal volume control

                            # Visual feedback for volume control
                            bar_height = int(frame.shape[0] * volume_level)
                            cv2.rectangle(frame, (frame.shape[1] - 50, frame.shape[0] - bar_height),
                                            (frame.shape[1] - 20, frame.shape[0]), (0, 255, 0), -1)
                            cv2.putText(frame, f"VOL: {int(volume_level * 100)}%", (frame.shape[1] - 150, 30),
                                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
                    else: # If palm not open, reset mouse tracking for smoother re-engagement
                        # These variables are now global, so just assign to them directly
                        # No 'nonlocal' needed within this block anymore for these variables
                        prev_mouse_x, prev_mouse_y = None, None # Reset to None
                        smooth_mouse_x, smooth_mouse_y = None, None # Reset to None

            # Display status
            if scroll_active:
                cv2.putText(frame, "SCROLLING", (10, 30),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)

            if gesture_state["mouse_control"]:
                 cv2.putText(frame, "MOUSE ACTIVE", (10, 60),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 0, 255), 2)

            cv2.putText(frame, "Press Q to quit", (10, 460),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)

            cv2.imshow("Gesture Control", frame)
            if cv2.waitKey(10) & 0xFF == ord('q'):
                gesture_state["active"] = False
                break

    cap.release()
    cv2.destroyAllWindows()