"""
Configuration parameters for the autonomous human tracking drone.
Adjust these values to tune tracking behavior.
"""

# === Video Settings ===
FRAME_WIDTH = 360
FRAME_HEIGHT = 240

# === PID Controller ===
PID_KP = 0.4       # Proportional gain (yaw responsiveness)
PID_KD = 0.4       # Derivative gain (dampens oscillation)
PID_KI = 0         # Integral gain (not used)

# === Distance Control ===
FB_RANGE_MIN = 3000   # Face area below this → move forward
FB_RANGE_MAX = 5000   # Face area above this → move backward
FB_SPEED = 25         # Forward/backward speed (cm/s)

# === Search Behavior ===
SEARCH_SPEED = 20     # Clockwise rotation speed (deg/s)
SEARCH_DELAY = 0.8    # Pause after search rotation (seconds)

# === Safety ===
MIN_BATTERY = 50      # Minimum battery percentage for takeoff
TAKEOFF_HEIGHT = 30   # Initial height after takeoff (cm)

# === Known Faces ===
# Add your reference face images here.
# Format: {"name": "path/to/image.jpg"}
# Place images in images/reference/ directory.
KNOWN_FACES = {
    "Person1": "images/reference/person1.jpg",
    "Person2": "images/reference/person2.jpg",
}
